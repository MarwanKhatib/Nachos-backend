from django.urls import path
from rest_framework.routers import DefaultRouter # Import DefaultRouter

from APIs.views.movie import (
    get_movie,
    MovieListView,
    MovieCommentViewSet, # Import the new ViewSet
)

router = DefaultRouter()
router.register(r'comments', MovieCommentViewSet, basename='movie-comment')

movie_urls = [
    path("", MovieListView.as_view(), name="movie-list"),
    path("<int:movie_id>/", get_movie, name="movie-detail"),
] + router.urls # Include router URLs
