from django.urls import path

from django.urls import path

from APIs.views import community as views

urlpatterns = [
    path("add-comment/", views.AddCommunityComment.as_view(), name="add-comment"),
    path(
        "delete-comment/<int:comment_id>/",
        views.DeleteCommunityComment.as_view(),
        name="delete-comment",
    ),
    path(
        "movie-comments/<int:movie_id>/",
        views.GetMovieComments.as_view(),
        name="movie-comments",
    ),
    path('watched-movies/<int:user_id>/', views.GetWatchedMovieIds.as_view(), name='watched-movies'),
]
