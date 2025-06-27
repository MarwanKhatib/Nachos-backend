from django.urls import path

from APIs.views.genre import get_all_genres, UserGenresView

genres_urls = [
    path("", get_all_genres, name="genre-list"),
    path("user/", UserGenresView.as_view(), name="user-genres"),
]
