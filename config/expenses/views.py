from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
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

class GroupInviteView(APIView):
    permission_classes = permissions.IsAuthenticated

    def post(self, request, id):
        group = get_object_or_404(Group, id=id)

        if(group.created_by)!=(request.user):
            return Response(
                {"detail" : "Only the group creator can invite members"},
                status = status.HTTP_403_FORBIDDEN       
                )
        
        user_id = request.data.get(user_id)
        user = get_object_or_404(User, id = id)

        if(GroupMember.filter(group = group,user = user).exists()):
            return Response(
                {"detail" : "User is already in the group"},
                status= status.HTTP_400_BAD_REQUEST,
            )
        
        GroupMember.objects.create(group=group, user=user)

        return Response(
            {"detail": "User added to the group successfully"},
            status= status.HTTP_201_CREATED
        )
