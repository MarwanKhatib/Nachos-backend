from django.urls import path
from ..views.user_views import UserViewSet

user_urls = [
    path('register/', UserViewSet.as_view({'post': 'create_user'}), name='register'),
    path('create-superuser/', UserViewSet.as_view({'post': 'create_superuser'}), name='create-superuser'),
    path('create-staff/', UserViewSet.as_view({'post': 'create_staff'}), name='create-staff'),
    path('verify/', UserViewSet.as_view({'post': 'verify'}), name='verify'),
    path('login/', UserViewSet.as_view({'post': 'login'}), name='login'),
    path('refresh-token/', UserViewSet.as_view({'post': 'refresh_token'}), name='refresh-token'),
    path('test-celery/', UserViewSet.as_view({'get': 'test_celery'}), name='test-celery'),
    path('<int:pk>/', UserViewSet.as_view({
        'get': 'retrieve',
        'put': 'update_user_info',
        'delete': 'destroy'
    }), name='user-detail'),
    path('all/', UserViewSet.as_view({'get': 'all_users'}), name='all-users'),
    path('<int:pk>/change-password/', UserViewSet.as_view({'put': 'change_password'}), name='change-password'),
    path('resend-verification-email/', UserViewSet.as_view({'post': 'resend_verification_email'}), name='resend-verification-email'),
]