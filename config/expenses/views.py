from django.shortcuts import render, get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    GroupSerializer,
    GroupMemberSerializer,
    JoinGroupSerializer,
    ExpenseSerializer,
    GroupDetailSerializer,
)
from .models import User, Group, GroupMember, Expense, ExpenseSplit
from decimal import Decimal
import traceback


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer



class GroupListCreateView(generics.ListCreateAPIView):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Group.objects.filter(members__user=self.request.user)

    def get_serializer_context(self):
        return {"request": self.request}

    def perform_create(self, serializer):
        group = serializer.save(created_by=self.request.user)
        GroupMember.objects.create(user=self.request.user, group=group)


class JoinGroupView(generics.CreateAPIView):
    serializer_class = JoinGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {"request": self.request}

    def perform_create(self, serializer):
        group_id = self.request.data.get("group_id")
        group = get_object_or_404(Group, id=group_id)
        serializer.save(user=self.request.user, group=group)


class GroupDetailView(generics.RetrieveAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupInviteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        group = get_object_or_404(Group, id=id)

        if group.created_by != request.user:
            return Response(
                {"detail": "Only the group creator can invite members"},
                status=status.HTTP_403_FORBIDDEN,
            )

        email = request.data.get("email")
        if not email:
            return Response(
                {"detail": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "User with this email does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if GroupMember.objects.filter(group=group, user=user).exists():
            return Response(
                {"detail": "User is already a member of this group"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        GroupMember.objects.create(group=group, user=user)

        return Response(
            {"detail": "User invited successfully"},
            status=status.HTTP_201_CREATED,
        )



class AddExpenseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        group = get_object_or_404(Group, id=request.data.get("group"))

        if not GroupMember.objects.filter(group=group, user=request.user).exists():
            return Response(
                {"detail": "You are not a member of this group"},
                status=status.HTTP_403_FORBIDDEN,
            )

        expense = serializer.save(
            paid_by=request.user,
            group=group,
        )

        splits = request.data.get("splits", [])

        try:
            self.handle_split(expense, splits)
        except ValueError as e:
            expense.delete()  # rollback expense
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ExpenseSerializer(expense).data,
            status=status.HTTP_201_CREATED,
        )

    def handle_split(self, expense, splits):
        members = GroupMember.objects.filter(group=expense.group)
        member_count = members.count()

        ExpenseSplit.objects.filter(expense=expense).delete()

        if expense.split_type == "equal":
            share = expense.amount / Decimal(member_count)

            for member in members:
                ExpenseSplit.objects.create(
                    expense=expense,
                    user=member.user,
                    share_amount=share,
                )

        elif expense.split_type == "custom":
            if not splits:
                raise ValueError("Splits are required for custom split")

            total = sum(Decimal(s["value"]) for s in splits)
            if total != expense.amount:
                raise ValueError("Custom split total must equal expense amount")

            for s in splits:
                ExpenseSplit.objects.create(
                    expense=expense,
                    user_id=s["user"],
                    share_amount=Decimal(s["value"]),
                )

        elif expense.split_type == "percentage":
            if not splits:
                raise ValueError("Splits are required for percentage split")

            total_percent = sum(Decimal(s["value"]) for s in splits)
            if total_percent != 100:
                raise ValueError("Percentage split must total 100%")

            for s in splits:
                share = (Decimal(s["value"]) / 100) * expense.amount
                ExpenseSplit.objects.create(
                    expense=expense,
                    user_id=s["user"],
                    share_amount=share,
                )

        else:
            raise ValueError("Invalid split type")


class GroupExpenseListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        group = get_object_or_404(Group, id=id)

        if not GroupMember.objects.filter(group=group, user=request.user).exists():
            return Response(
                {"detail": "Not a group member"},
                status=status.HTTP_403_FORBIDDEN,
            )

        expenses = Expense.objects.filter(group=group).order_by("-created_at")
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)



class GroupDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        group = get_object_or_404(Group, id=id)

        if not GroupMember.objects.filter(group=group, user=request.user).exists():
            return Response(
                {"detail": "Not a group member"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            serializer = GroupDetailSerializer(group)
            return Response(serializer.data)
        except Exception as e:
            print("Group detail error:", e)
            print(traceback.format_exc())
            return Response(
                {"detail": f"Error loading group details: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GroupBalancesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        group = get_object_or_404(Group, id=id)

        if not GroupMember.objects.filter(group=group, user=request.user).exists():
            return Response(
                {"detail": "Not a group member"},
                status=status.HTTP_403_FORBIDDEN,
            )

        members = GroupMember.objects.filter(group=group).select_related("user")
        net = {member.user_id: Decimal("0.00") for member in members}
        users = {member.user_id: member.user for member in members}

        splits = ExpenseSplit.objects.filter(expense__group=group).select_related(
            "expense", "user"
        )
        for split in splits:
            payer_id = split.expense.paid_by_id
            debtor_id = split.user_id
            amount = split.share_amount

            net[payer_id] = net.get(payer_id, Decimal("0.00")) + amount
            net[debtor_id] = net.get(debtor_id, Decimal("0.00")) - amount

        settlements = self._minimize_settlements(net)

        balances = []
        for user_id, balance in net.items():
            balances.append(
                {
                    "user_id": user_id,
                    "name": users[user_id].name,
                    "email": users[user_id].email,
                    "net_balance": float(balance.quantize(Decimal("0.01"))),
                }
            )

        return Response(
            {
                "group_id": group.id,
                "group_name": group.name,
                "currency": group.currency,
                "balances": balances,
                "settlements": settlements,
            }
        )

    def _minimize_settlements(self, net):
        creditors = []
        debtors = []

        for user_id, balance in net.items():
            rounded = balance.quantize(Decimal("0.01"))
            if rounded > 0:
                creditors.append([user_id, rounded])
            elif rounded < 0:
                debtors.append([user_id, -rounded])

        i = 0
        j = 0
        optimized = []

        while i < len(debtors) and j < len(creditors):
            debtor_id, owes = debtors[i]
            creditor_id, gets = creditors[j]
            amount = min(owes, gets).quantize(Decimal("0.01"))

            if amount > 0:
                optimized.append(
                    {
                        "from_user": debtor_id,
                        "to_user": creditor_id,
                        "amount": float(amount),
                    }
                )

            debtors[i][1] = (owes - amount).quantize(Decimal("0.01"))
            creditors[j][1] = (gets - amount).quantize(Decimal("0.01"))

            if debtors[i][1] == 0:
                i += 1
            if creditors[j][1] == 0:
                j += 1

        return optimized
