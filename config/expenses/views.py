from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, UserSerializer, GroupSerializer, GroupMemberSerializer
from .models import User, Group, GroupMember

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
    
    def perform_create(self, serializer):
        group = serializer.save(created_by = self.request.user)
        GroupMember.objects.create(
            user = self.request.user,
            group = group
        )