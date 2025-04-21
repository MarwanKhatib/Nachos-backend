from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import *
urlpatterns = [
    path("", hello_world),
    path("register/", RegisterUserView.as_view(), name="register"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("select-genres/", SelectGenresView.as_view(), name="select-genres"),
    path("user-genres/<int:user_id>/", GetUserGenresView.as_view(), name="user-genres"),
    path("user-suggestions/<int:user_id>/",GetTop10Suggestion.as_view(),name="user-suggestions",),
    path("movie-infos/<int:movie_id>/",GetMovie.as_view(),name="movie-infos",)
]
