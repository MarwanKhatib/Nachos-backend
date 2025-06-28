from django.urls import path
from APIs.views.watchlist import WatchlistView, WatchlistManageView

watchlist_urls = [
    path('', WatchlistView.as_view(), name='watchlist-list'),  
    path('<int:movie_id>/', WatchlistManageView.as_view(), name='watchlist-manage'), 
]