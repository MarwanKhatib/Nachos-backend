from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import *

urlpatterns = [
    # General Routes
    path("", hello_world, name="hello-world"),
    path("register/", register_user, name="register"),
    path("verify-email/", verify_email, name="verify-email"),
    
    # JWT Authentication
    path("token/", custom_token_obtain_pair, name="token_obtain_pair"),
    path("token/refresh/", custom_token_refresh, name="token_refresh"),
    
    # Genre Selection and User Preferences
    path("select-genres/", select_genres, name="select-genres"),
    path("user-genres/<int:user_id>/", get_user_genres, name="user-genres"),
    
    # Movie Suggestions and Details
    path("user-suggestions/<int:user_id>/", get_top_10_suggestions, name="user-suggestions"),
    path("movie-infos/<int:movie_id>/", get_movie, name="movie-infos"),
    path("add-to-watchlist/", add_to_watchlist, name="add_to_watchlist"),
    path("watchlist/<int:user_id>/", get_watchlist, name="get_watchlist"),
    path("remove-from-watchlist/", remove_from_watchlist, name="remove_from_watchlist"),
    path("rate-movie/", rate_movie, name="rate_movie"),
]