from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.db import models
from .models import User, Group, GroupMember, Expense

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only = True, required = True, validators = [validate_password])
    password2 = serializers.CharField(write_only = True, required = True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'name', 'password', 'password2', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate(self, attrs):
        if (attrs['password']!=attrs['password2']):
            raise serializers.ValidationError({"password":"passwords did not match"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

class GroupSerializer(serializers.ModelSerializer):
    members_count = serializers.IntegerField(
    source='members.count', read_only=True)
    created_by = serializers.IntegerField(
        source = 'created_by.id', read_only = True)
    is_creator = serializers.SerializerMethodField()
    class Meta:
        model = Group
        fields = ('id', 'name', 'currency', 'members_count', 'created_by', 'is_creator', 'created_at')
    
    def get_is_creator(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.created_by == request.user
        return False

class GroupMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMember
        fields = ('id', 'group', 'joined_at')

class JoinGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMember
        fields = ('id', 'group', 'user', 'joined_at')
        read_only_fields = ('id', 'joined_at')

class ExpenseSerializer(serializers.ModelSerializer):
    paid_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Expense
        fields = ('id', 'group', 'paid_by', 'paid_by_name', 'amount', 'description', 'split_type', 'created_at')
        read_only_fields = ('paid_by', 'created_at')
    
    def get_paid_by_name(self, obj):
        return obj.paid_by.name if obj.paid_by else None

class GroupMemberNameSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.name")

    class Meta:
        model = GroupMember
        fields = ["id", "name"]

class GroupDetailSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    total_expense = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "currency",
            "members",
            "members_count",
            "total_expense",
        )

    def get_members(self, obj):
        try:
            group_members = obj.members.all()
            serializer = GroupMemberNameSerializer(group_members, many=True)
            return serializer.data
        except Exception as e:
            print(f"Error in get_members: {e}")
            return []

    def get_members_count(self, obj):
        return obj.members.count()

    def get_total_expense(self, obj):
        return (
            Expense.objects.filter(group=obj)
            .aggregate(total=models.Sum("amount"))["total"]
            or 0
        )


