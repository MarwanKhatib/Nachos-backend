from django.urls import path
from APIs.views.watchlist import WatchlistView

watchlist_urls = [
    path('', WatchlistView.as_view(), name='watchlist'),
]
