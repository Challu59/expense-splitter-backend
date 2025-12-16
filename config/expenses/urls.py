from django.urls import path
from .views import CustomTokenObtainPairView, RegisterView

urlpatterns = [
    path('auth/login/', CustomTokenObtainPairView.as_view(), name= 'login'),
    path('auth/register/', RegisterView.as_view())
]