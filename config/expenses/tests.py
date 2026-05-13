from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Expense, ExpensePayment, ExpenseSplit, Group, GroupMember, Settlement, User


class SettlementAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.alice = User.objects.create_user(
            email="alice@test.com",
            username="alice",
            password="testpass123",
            name="Alice",
        )
        self.bob = User.objects.create_user(
            email="bob@test.com",
            username="bob",
            password="testpass123",
            name="Bob",
        )
        self.group = Group.objects.create(name="Trip", created_by=self.alice)
        GroupMember.objects.create(user=self.alice, group=self.group)
        GroupMember.objects.create(user=self.bob, group=self.group)

        # Bob paid 100; equal split → Alice owes Bob 50 (net: Alice -50, Bob +50)
        expense = Expense.objects.create(
            group=self.group,
            paid_by=self.bob,
            amount=Decimal("100.00"),
            description="Dinner",
            split_type="equal",
        )
        ExpensePayment.objects.create(expense=expense, user=self.bob, amount=Decimal("100.00"))
        ExpenseSplit.objects.create(expense=expense, user=self.alice, share_amount=Decimal("50.00"))
        ExpenseSplit.objects.create(expense=expense, user=self.bob, share_amount=Decimal("50.00"))

    def test_post_settlement_global_url(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(
            "/api/settlements/",
            {
                "group": self.group.id,
                "to_user": self.bob.id,
                "amount": "50.00",
                "note": "Cash",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["from_user"], self.alice.id)
        self.assertEqual(response.data["to_user"], self.bob.id)
        self.assertEqual(response.data["note"], "Cash")
        self.assertEqual(Settlement.objects.filter(group=self.group).count(), 1)

    def test_post_settlement_group_scoped_url(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(
            f"/api/groups/{self.group.id}/settlements/",
            {"to_user": self.bob.id, "amount": "50.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["group"], self.group.id)

    def test_settlement_rejected_when_payer_not_in_debt(self):
        self.client.force_authenticate(user=self.bob)
        response = self.client.post(
            "/api/settlements/",
            {"group": self.group.id, "to_user": self.alice.id, "amount": "10.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_group_settlements_requires_membership(self):
        outsider = User.objects.create_user(
            email="out@test.com",
            username="out",
            password="testpass123",
            name="Out",
        )
        self.client.force_authenticate(user=outsider)
        response = self.client.get(f"/api/groups/{self.group.id}/settlements/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
