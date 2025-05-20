from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from ..views import *

urlpatterns = [
    # User routes
    path('user/', include('APIs.urls.user_urls')),
    
    # Movie routes
    # path('movie/', include([
    #     path('select-genres/', select_genres, name='select-genres'),
    #     path('user-genres/<int:user_id>/', get_user_genres, name='user-genres'),
    #     path('user-suggestions/<int:user_id>/', get_top_10_suggestions, name='user-suggestions'),
    #     path('movie-infos/<int:movie_id>/', get_movie, name='movie-infos'),
    #     path('add-to-watchlist/', add_to_watchlist, name='add_to_watchlist'),
    #     path('watchlist/<int:user_id>/', get_watchlist, name='get_watchlist'),
    #     path('remove-from-watchlist/', remove_from_watchlist, name='remove_from_watchlist'),
    #     path('rate-movie/', rate_movie, name='rate_movie'),
    # ])),
    
    # # Community routes
    # path('community/', include([
    #     path('add-comment/', add_community_comment, name='add_community_comment'),
    #     path('delete-comment/<int:comment_id>/', delete_community_comment, name='delete_community_comment'),
    #     path('movie-comments/<int:movie_id>/', get_movie_comments, name='get_movie_comments'),
    #     path('watched-movies/<int:user_id>/', get_watched_movie_ids, name='get_watched_movie_ids'),
    # ])),
    
    # # Social platform routes
    # path('social/', include([
    #     path('create-group/', create_group, name='create_group'),
    #     path('join-group/', join_group, name='join_group'),
    #     path('block-user/', block_user, name='block_user'),
    #     path('blocked-users/', get_blocked_users, name='get_blocked_users'),
    #     path('unblock-user/', unblock_user, name='unblock_user'),
    #     path('write-post/', write_post, name='write_post'),
    #     path('delete-post/', delete_post, name='delete_post'),
    #     path('like-post/', like_post, name='like_post'),
    #     path('unlike-post/', unlike_post, name='unlike_post'),
    #     path('comment-post/', comment_on_post, name='comment_post'),
    #     path('edit-comment/', edit_comment, name='edit_comment'),
    #     path('delete-comment/', delete_comment, name='delete_comment'),
    #     path('group-posts/<int:group_id>/', get_group_posts, name='get_group_posts'),
    #     path('user-group-posts/<int:user_id>/', get_user_group_posts, name='get_user_group_posts'),
    #     path('leave-group/', leave_group, name='leave_group'),
    # ])),
] 