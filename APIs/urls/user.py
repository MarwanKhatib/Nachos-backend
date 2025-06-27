"""
User-related API endpoints for registration, authentication, profile management, and admin user management.
Grouped by authentication, profile, and admin actions.
"""
from django.urls import path
from APIs.views.user import UserViewSet

# Authenticated User Profile Management URLs (self-service)
user_profile_urls = [
    path('', UserViewSet.as_view({'get': 'retrieve'}), name='user-profile-retrieve'),
    path('edit/', UserViewSet.as_view({'put': 'update'}), name='user-profile-update'),
    path('delete/', UserViewSet.as_view({'delete': 'destroy'}), name='user-profile-delete'),
    path('change-password/', UserViewSet.as_view({'put': 'change_password'}), name='user-change-password'),
    path('movie-suggestions/', UserViewSet.as_view({'get': 'get_suggestions'}), name='movie-suggestions'), # New endpoint
    path('upload-profile-picture/', UserViewSet.as_view({'post': 'upload_profile_picture'}), name='user-upload-profile-picture'), # New endpoint
]

# Admin User Management URLs
admin_user_urls = [
    path('users/', UserViewSet.as_view({'get': 'all_users'}), name='admin-users-list'),
    path('users/<int:pk>/', UserViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    }), name='admin-user-detail'),
    path('users/<int:pk>/change-password/', UserViewSet.as_view({'put': 'change_password'}), name='admin-user-change-password'),
    path('create-superuser/', UserViewSet.as_view({'post': 'create_superuser'}), name='admin-create-superuser'),
    path('create-staff/', UserViewSet.as_view({'post': 'create_staff'}), name='admin-create-staff'),
]

# Combine all URLs
user_urls = user_profile_urls
