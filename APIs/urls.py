from . import views
from django.urls import path

urlpatterns = [
    path("v1/delete-user/", views.delete_user, name="delete_user"),
    path("v1/update-user/", views.update_user, name="update_user"),
    path("v1/create-user/", views.create_user, name="create_user"),
    path("v1/get-users/", views.get_users, name="get_users"),
    path("v1/get-csrf-token/", views.get_csrf_token, name="get_csrf_token"),
    path("v1/fetch-user-token/", views.fetch_user_token, name="fetch_user_token"),
    path("v1/login/", views.login_user, name="login_user"),
]
