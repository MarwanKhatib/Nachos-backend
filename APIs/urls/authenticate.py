from django.urls import path
from APIs.views.authenticate import AuthenticationViewSet

auth_urls = [
    path('register/', AuthenticationViewSet.as_view({'post': 'create_user'}), name='auth-register'),
    path('verify-email/', AuthenticationViewSet.as_view({'post': 'verify'}), name='auth-verify-email'),
    path('login/', AuthenticationViewSet.as_view({'post': 'login'}), name='auth-login'),
    path('refresh-token/', AuthenticationViewSet.as_view({'post': 'refresh_token'}), name='auth-refresh-token'),
    path('resend-verification-email/', AuthenticationViewSet.as_view({'post': 'resend_verification_email'}), name='auth-resend-verification-email'),
    path('request-password-reset/', AuthenticationViewSet.as_view({'post': 'request_password_reset'}), name='auth-request-password-reset'),
    path('verify-password-reset-code/', AuthenticationViewSet.as_view({'post': 'verify_password_reset_code'}), name='auth-verify-password-reset-code'), # New endpoint
    path('set-new-password/', AuthenticationViewSet.as_view({'post': 'set_new_password'}), name='auth-set-new-password'),
    path('logout/', AuthenticationViewSet.as_view({'post': 'logout'}), name='auth-logout'),
]
