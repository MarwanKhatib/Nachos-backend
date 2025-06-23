"""
User-related API endpoints for registration, authentication, profile management, and admin user management.
Grouped by authentication, profile, and admin actions.
"""
from django.urls import path
from ..views.user_views import UserViewSet

# Authentication and Registration URLs
user_auth_urls = [
    path('register/', UserViewSet.as_view({'post': 'create_user'}), name='user-register'),
    path('verify-email/', UserViewSet.as_view({'post': 'verify'}), name='user-verify-email'),
    path('login/', UserViewSet.as_view({'post': 'login'}), name='user-login'),
    path('refresh-token/', UserViewSet.as_view({'post': 'refresh_token'}), name='user-refresh-token'),
    path('resend-verification-email/', UserViewSet.as_view({'post': 'resend_verification_email'}), name='user-resend-verification-email'),
]

# Authenticated User Profile Management URLs (self-service)
user_profile_urls = [
    path('profile/', UserViewSet.as_view({'get': 'retrieve'}), name='user-profile-retrieve'),
    path('profile/edit/', UserViewSet.as_view({'put': 'update'}), name='user-profile-update'),
    path('profile/delete/', UserViewSet.as_view({'delete': 'destroy'}), name='user-profile-delete'),
    path('profile/change-password/', UserViewSet.as_view({'put': 'change_password'}), name='user-profile-change-password'),
]

# Admin User Management URLs
admin_user_urls = [
    path('admin/users/all/', UserViewSet.as_view({'get': 'all_users'}), name='admin-users-all'),
    path('admin/users/<int:pk>/', UserViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    }), name='admin-user-detail'),
    path('admin/users/<int:pk>/change-password/', UserViewSet.as_view({'put': 'change_password'}), name='admin-user-change-password'),
    path('admin/create-superuser/', UserViewSet.as_view({'post': 'create_superuser'}), name='admin-create-superuser'),
    path('admin/create-staff/', UserViewSet.as_view({'post': 'create_staff'}), name='admin-create-staff'),
]

# Combine all URLs
user_urls = user_auth_urls + user_profile_urls + admin_user_urls
