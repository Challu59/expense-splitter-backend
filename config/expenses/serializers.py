from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User, Group, GroupMember

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
    class Meta:
        model = Group
        fields = ('id', 'name', 'currency', 'members_count', 'created_at')

class GroupMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMember
        fields = ('id', 'group', 'joined_at')

class JoinGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMember
        fields = ('id', 'group', 'user', 'joined_at')
        read_only_fields = ('id', 'joined_at')

