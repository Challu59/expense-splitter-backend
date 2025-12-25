from django.urls import path
from .views import CustomTokenObtainPairView, RegisterView, GroupListCreateView, GroupDetailView, GroupInviteView, AddExpenseView, GroupExpenseListView, GroupDetailAPIView

urlpatterns = [
    path('auth/login/', CustomTokenObtainPairView.as_view(), name= 'login'),
    path('auth/register/', RegisterView.as_view()),
    path('groups/', GroupListCreateView.as_view()),
    path('groups/<int:id>', GroupDetailView.as_view()),
    path('groups/<int:id>/invite', GroupInviteView.as_view()),
    path("expenses/", AddExpenseView.as_view()),
    path("groups/<int:id>/expenses/", GroupExpenseListView.as_view()),
    path("groups/<int:id>/detail/", GroupDetailAPIView.as_view()),
]