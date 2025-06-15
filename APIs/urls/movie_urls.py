from django.urls import path

from APIs.views.movie_views import get_movie

movie_urls = [
    # path("select-genres/", select_genres, name="select-genres"),
    # path("user-genres/<int:user_id>/", get_user_genres, name="user-genres"),
    # path(
    #     "user-suggestions/<int:user_id>/",
    #     get_top_10_suggestions,
    #     name="user-suggestions",
    # ),
    # path("add-to-watchlist/", add_to_watchlist, name="add_to_watchlist"),
    # path("watchlist/<int:user_id>/", get_watchlist, name="get_watchlist"),
    # path("remove-from-watchlist/", remove_from_watchlist, name="remove_from_watchlist"),
    # path("rate-movie/", rate_movie, name="rate_movie"),
    path("<int:movie_id>/", get_movie, name="get_movie"),
]
