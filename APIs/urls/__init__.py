from django.urls import path, include

urlpatterns = [
    path('user/', include('APIs.urls.user')),
    path('movies/', include('APIs.urls.movie')),
    path('genres/', include('APIs.urls.genres')),
    path('watchlist/', include('APIs.urls.watchlist')),
    path('auth/', include('APIs.urls.authenticate')),
]
