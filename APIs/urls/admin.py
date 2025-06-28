from django.urls import path
from APIs.views.admin import DashboardView, UserListAPIView, UserDetailAPIView, UserCreateAPIView, SuperuserCreateAPIView, StaffUserCreateAPIView
from APIs.views.user import UserViewSet # Import UserViewSet for admin-related user views

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='admin-dashboard'),
    # Admin User Management URLs (moved from APIs/urls/user.py)
    path('users/', UserListAPIView.as_view(), name='admin-user-list'), # List all users
    path('users/create/', UserCreateAPIView.as_view(), name='admin-user-create'), # For creating normal users by admin
    path('users/create-superuser/', SuperuserCreateAPIView.as_view(), name='admin-create-superuser'), # For creating superusers by admin
    path('users/create-staff/', StaffUserCreateAPIView.as_view(), name='admin-create-staff'), # For creating staff users by admin
    path('users/<int:id>/', UserDetailAPIView.as_view(), name='admin-user-detail'), # Retrieve/Update/Delete user by ID
    path('users/<int:pk>/change-password/', UserViewSet.as_view({'put': 'change_password'}), name='admin-user-change-password'), # Admin change password for a user
]
