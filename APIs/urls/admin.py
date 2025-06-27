from django.urls import path
from APIs.views.admin import DashboardView, UserListAPIView, UserDetailAPIView, UserCreateAPIView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='admin-dashboard'),
    path('users/', UserListAPIView.as_view(), name='admin-user-list'),
    path('users/create/', UserCreateAPIView.as_view(), name='admin-user-create'),
    path('users/<int:id>/', UserDetailAPIView.as_view(), name='admin-user-detail'),
]
