# users/urls.py
from django.urls import path
from .views import UserListCreateView, UserDetailView, UserProfileView

urlpatterns = [
    # Routes pour Admin/RH
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/me/', UserProfileView.as_view(), name='user-profile'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),  
]