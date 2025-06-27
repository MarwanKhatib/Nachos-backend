from django.urls import path

from django.urls import path

from APIs.views import group as views

urlpatterns = [
    path("create/", views.CreateGroup.as_view(), name="group-create"),
    path("join/", views.JoinGroup.as_view(), name="group-join"),
    path("block-user/", views.BlockUser.as_view(), name="group-block-user"),
    path("blocked-users/", views.GetBlockedUsers.as_view(), name="group-blocked-users"),
    path("unblock-user/", views.UnblockUser.as_view(), name="group-unblock-user"),
    path("write-post/", views.WritePost.as_view(), name="group-write-post"),
    path("delete-post/", views.DeletePost.as_view(), name="group-delete-post"),
    path("like-post/", views.LikePost.as_view(), name="group-like-post"),
    path("unlike-post/", views.UnlikePost.as_view(), name="group-unlike-post"),
    path("comment-on-post/", views.CommentOnPost.as_view(), name="group-comment-on-post"),
    path("delete-comment/", views.DeleteComment.as_view(), name="group-delete-comment"),
    path("edit-comment/", views.EditComment.as_view(), name="group-edit-comment"),
    path("posts/<int:group_id>/", views.GetGroupPosts.as_view(), name="group-posts"),
    path("user-posts/<int:user_id>/", views.GetUserGroupPosts.as_view(), name="group-user-posts"),
    path("leave/", views.LeaveGroup.as_view(), name="group-leave"),
]
