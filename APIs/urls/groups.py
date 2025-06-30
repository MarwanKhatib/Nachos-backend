from django.urls import path

from APIs.views import group as views

urlpatterns = [
    # Groups Management
    path("", views.GetAllGroups.as_view(), name="group-list"),
    path("create/", views.CreateGroup.as_view(), name="group-create"),
    path("<int:group_id>/join/", views.JoinGroup.as_view(), name="group-join"),
    path("<int:group_id>/leave/", views.LeaveGroup.as_view(), name="group-leave"),
    path("<int:group_id>/", views.DeleteGroup.as_view(), name="group-delete"),
    path("edit/<int:group_id>/", views.EditGroup.as_view(), name="group-edit"), 
    
    # Groups User Management
    path("users/block/", views.BlockUser.as_view(), name="group-user-block"),
    path("users/blocked/", views.GetBlockedUsers.as_view(), name="group-blocked-users-list"),
    path("users/unblock/", views.UnblockUser.as_view(), name="group-user-unblock"),
    
    # Posts Management
    path("<int:group_id>/posts/", views.GetGroupPosts.as_view(), name="group-post-list"),
    path("users/<int:user_id>/posts/", views.GetUserGroupPosts.as_view(), name="group-user-post-list"),
    path("<int:group_id>/posts/create/", views.WritePost.as_view(), name="group-post-create"),
    path("<int:group_id>/posts/<int:post_id>/", views.DeletePost.as_view(), name="group-post-delete"),
    path("<int:group_id>/posts/edit/<int:post_id>/", views.EditPost.as_view(), name="group-post-edit"),
    
    # Posts Comment Management
    path("<int:group_id>/posts/<int:post_id>/comments/", views.GetAllCommentsForPost.as_view(), name="group-post-comments-list"),
    path("<int:group_id>/posts/<int:post_id>/comments/create/", views.CommentOnPost.as_view(), name="group-post-comment-create"),
    path("<int:group_id>/posts/<int:post_id>/comments/delete/<int:comment_id>/", views.DeleteComment.as_view(), name="group-post-comment-delete"),
    path("<int:group_id>/posts/<int:post_id>/comments/edit/<int:comment_id>/", views.EditComment.as_view(), name="group-post-comment-edit"),
   
    # Posts Like Management
    path("<int:group_id>/posts/<int:post_id>/unlike/", views.UnlikePost.as_view(), name="group-post-unlike"),
    path("<int:group_id>/posts/<int:post_id>/like/", views.LikePost.as_view(), name="group-post-like"),
    path("my_groups/", views.MyGroups.as_view(), name="my_groups"),
]
