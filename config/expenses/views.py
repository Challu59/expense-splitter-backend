from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, UserSerializer, GroupSerializer, GroupMemberSerializer, JoinGroupSerializer, ExpenseSerializer
from .models import User, Group, GroupMember, Expense, ExpenseSplit
from django.shortcuts import get_object_or_404
from decimal import Decimal

# Create your views here.

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class GroupListCreateView(generics.ListCreateAPIView):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (Group.objects.filter
                (
            members__user = self.request.user
        )
        )
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    def perform_create(self, serializer):
        group = serializer.save(created_by = self.request.user)
        GroupMember.objects.create(
            user = self.request.user,
            group = group
        )

class JoinGroupView(generics.CreateAPIView):
    serializer_class = JoinGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {'request': self.request}
    
    def perform_create(self, serializer):
        group_id = self.request.data.get('group_id')
        group = get_object_or_404(Group, id = group_id)
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
                status=status.HTTP_403_FORBIDDEN
            )

        email = request.data.get("email")
        if not email:
            return Response(
                {"detail": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "User with this email does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

        if GroupMember.objects.filter(group=group, user=user).exists():
            return Response(
                {"detail": "User is already a member of this group"},
                status=status.HTTP_400_BAD_REQUEST
            )

        GroupMember.objects.create(
            group=group,
            user=user
        )

        return Response(
            {"detail": "User invited successfully"},
            status=status.HTTP_201_CREATED
        )

class AddExpenseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        group = get_object_or_404(Group, id=request.data.get("group"))

        if not GroupMember.objects.filter(group=group, user=request.user).exists():
            return Response(
                {"detail": "You are not a member of this group"},
                status=status.HTTP_403_FORBIDDEN
            )

        expense = serializer.save(
            paid_by=request.user,
            group=group
        )

        self.handle_split(expense)

        return Response(
            ExpenseSerializer(expense).data,
            status=status.HTTP_201_CREATED
        )

    def handle_split(self, expense):
        members = GroupMember.objects.filter(group=expense.group)
        member_count = members.count()

        if expense.split_type == "equal":
            share = expense.amount / Decimal(member_count)

            for member in members:
                ExpenseSplit.objects.create(
                    expense=expense,
                    user=member.user,
                    share_amount=share
                )

