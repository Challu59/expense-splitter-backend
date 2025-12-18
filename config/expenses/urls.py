from django.urls import path
from .views import CustomTokenObtainPairView, RegisterView, GroupListCreateView

urlpatterns = [
    path('auth/login/', CustomTokenObtainPairView.as_view(), name= 'login'),
    path('auth/register/', RegisterView.as_view()),
    path('groups/', GroupListCreateView.as_view()),
]