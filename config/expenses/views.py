from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, UserSerializer, GroupSerializer, GroupMemberSerializer, JoinGroupSerializer
from .models import User, Group, GroupMember
from django.shortcuts import get_object_or_404

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

class JoinGroupView(generics.CreateAPIView):
    serializer_class = JoinGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        group_id = self.request.data.get('group_id')
        group = get_object_or_404(Group, id = group_id)
        serializer.save(user=self.request.user, group=group)

class GroupDetailView(generics.RetrieveAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]
