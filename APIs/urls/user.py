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
    path('movie-suggestions/', UserViewSet.as_view({'get': 'get_suggestions'}), name='movie-suggestions'),
    path('top-10-suggestions/', UserViewSet.as_view({'get': 'get_top_10_suggestions'}), name='top-10-movie-suggestions'), # New endpoint for top 10
    path('upload-profile-picture/', UserViewSet.as_view({'post': 'upload_profile_picture'}), name='user-upload-profile-picture'),
]

# Combine all URLs
user_urls = user_profile_urls
