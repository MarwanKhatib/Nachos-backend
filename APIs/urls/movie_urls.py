from django.urls import path

from APIs.views.movie_views import (
    add_to_watchlist,
    get_movie,
    get_top_10_suggestions,
    get_user_genres,
    get_watchlist,
    rate_movie,
    remove_from_watchlist,
    select_genres,
)

movie_urls = [
    path("<int:movie_id>/", get_movie, name="get_movie"),
    path("add-to-watchlist/", add_to_watchlist, name="add_to_watchlist"),
    path("user-genres/", get_user_genres, name="user-genres"),
    path(
        "user-suggestions/",
        get_top_10_suggestions,
        name="user-suggestions",
    ),
    path("watchlist/", get_watchlist, name="get_watchlist"),
    path("remove-from-watchlist/", remove_from_watchlist, name="remove_from_watchlist"),
    path("select-genres/", select_genres, name="select-genres"),
    path("rate-movie/", rate_movie, name="rate_movie"),
]
