import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.apps import apps
from django.db.models import signals

# Manually import models to ensure they are loaded
Group = apps.get_model('APIs', 'Group')
User = apps.get_model('APIs', 'User')
UserGroup = apps.get_model('APIs', 'UserGroup')
Post = apps.get_model('APIs', 'Post')
UserPost = apps.get_model('APIs', 'UserPost')
UserComment = apps.get_model('APIs', 'UserComment')
UserReact = apps.get_model('APIs', 'UserReact')


from APIs.serializers.group_serializers import (
    CreateGroupSerializer,
    JoinGroupSerializer,
    BlockUserSerializer,
    UnblockUserSerializer,
    WritePostSerializer,
    CommentPostSerializer,
    EditCommentSerializer,
)

logger = logging.getLogger(__name__)


class CreateGroup(APIView):
    def post(self, request):
        user_id_req = request.data.get("user_id")
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for creating a group.")
        
        serializer = CreateGroupSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Create group failed for user {user_id_req} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data["user_id"]
        group_name = serializer.validated_data["group_name"]
        description = serializer.validated_data["description"]
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.warning(f"Create group failed for user {user_id_req} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Create the group
            group = Group.objects.create(name=group_name, description=description)

            # Add the user to the group as an admin
            UserGroup.objects.create(user=user, group=group, is_admin=True, is_blocked=False)
            logger.info(f"Group '{group_name}' created successfully by user {user_id_req} to {path}.")
            return Response(
                {"message": "Group created successfully.", "group_id": group.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Create group failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JoinGroup(APIView):
    def post(self, request):
        user_id_req = request.data.get("user_id")
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for joining a group.")
        
        serializer = JoinGroupSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Join group failed for user {user_id_req} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data["user_id"]
        group_id = serializer.validated_data["group_id"]

        try:
            user = User.objects.get(id=user_id)
            group = Group.objects.get(id=group_id)
        except User.DoesNotExist:
            logger.warning(f"Join group failed for user {user_id_req} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            logger.warning(f"Join group failed for user {user_id_req} to {path}: Group not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Add the user to the group
            UserGroup.objects.create(user=user, group=group, is_admin=False, is_blocked=False)
            logger.info(f"User {user_id_req} joined group {group_id} successfully to {path}.")
            return Response(
                {"message": "User joined the group successfully."},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Join group failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BlockUser(APIView):
    def post(self, request):
        admin_user_id_req = request.data.get("admin_user_id")
        path = request.path
        logger.info(f"Request by admin {admin_user_id_req} to {path} for blocking a user.")
        
        serializer = BlockUserSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Block user failed for admin {admin_user_id_req} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        admin_user_id = serializer.validated_data["admin_user_id"]
        group_id = serializer.validated_data["group_id"]
        blocked_user_id = serializer.validated_data["blocked_user_id"]

        try:
            # Get the UserGroup entry for the blocked user
            user_group = UserGroup.objects.get(user_id=blocked_user_id, group_id=group_id)

            # Block the user
            user_group.is_blocked = True
            user_group.save()
            logger.info(f"User {blocked_user_id} blocked successfully by admin {admin_user_id_req} in group {group_id} to {path}.")
            return Response(
                {"message": "User blocked successfully."}, status=status.HTTP_200_OK
            )
        except UserGroup.DoesNotExist:
            logger.warning(f"Block user failed for admin {admin_user_id_req} to {path}: User {blocked_user_id} not in group {group_id}.")
            return Response({"error": "User not found in this group."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Block user failed for admin {admin_user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetBlockedUsers(APIView):
    def get(self, request):
        admin_id_req = request.query_params.get("admin_id")
        group_id_req = request.query_params.get("group_id")
        path = request.path
        logger.info(f"Request by admin {admin_id_req} to {path} for getting blocked users in group {group_id_req}.")
        
        admin_id = admin_id_req
        group_id = group_id_req

        # Validate admin user and group
        try:
            admin = UserGroup.objects.get(
                user_id=admin_id, group_id=group_id, is_admin=True
            )
        except UserGroup.DoesNotExist:
            logger.warning(f"Get blocked users failed for admin {admin_id_req} to {path}: Not an admin of group {group_id_req}.")
            return Response(
                {"error": "You are not an admin of this group."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Fetch blocked users in the group
            blocked_users = UserGroup.objects.filter(
                group_id=group_id, is_blocked=True
            ).select_related("user")
            blocked_user_data = [
                {"user_id": u.user.id, "username": u.user.username} for u in blocked_users
            ]
            logger.info(f"Blocked users retrieved successfully by admin {admin_id_req} in group {group_id_req} to {path}.")
            return Response({"blocked_users": blocked_user_data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Get blocked users failed for admin {admin_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UnblockUser(APIView):
    def post(self, request):
        admin_user_id_req = request.data.get("admin_user_id")
        path = request.path
        logger.info(f"Request by admin {admin_user_id_req} to {path} for unblocking a user.")
        
        serializer = UnblockUserSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Unblock user failed for admin {admin_user_id_req} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        admin_user_id = serializer.validated_data["admin_user_id"]
        group_id = serializer.validated_data["group_id"]
        unblocked_user_id = serializer.validated_data["unblocked_user_id"]

        try:
            # Get the UserGroup entry for the unblocked user
            user_group = UserGroup.objects.get(user_id=unblocked_user_id, group_id=group_id)

            # Unblock the user
            user_group.is_blocked = False
            user_group.save()
            logger.info(f"User {unblocked_user_id} unblocked successfully by admin {admin_user_id_req} in group {group_id} to {path}.")
            return Response(
                {"message": "User unblocked successfully."}, status=status.HTTP_200_OK
            )
        except UserGroup.DoesNotExist:
            logger.warning(f"Unblock user failed for admin {admin_user_id_req} to {path}: User {unblocked_user_id} not found in group {group_id}.")
            return Response({"error": "User not found in this group."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unblock user failed for admin {admin_user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WritePost(APIView):
    def post(self, request):
        user_id_req = request.data.get("user_id")
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for writing a post.")
        
        serializer = WritePostSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Write post failed for user {user_id_req} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data["user_id"]
        group_id = serializer.validated_data["group_id"]
        content = serializer.validated_data["content"]

        try:
            user = User.objects.get(id=user_id)
            group = Group.objects.get(id=group_id)
        except User.DoesNotExist:
            logger.warning(f"Write post failed for user {user_id_req} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            logger.warning(f"Write post failed for user {user_id_req} to {path}: Group not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Create the post
            post = Post.objects.create(content=content, reaction_no=0, comment_no=0)

            # Link the post to the user and group
            UserPost.objects.create(user=user, group=group, post=post)
            logger.info(f"Post created successfully by user {user_id_req} in group {group_id} to {path}.")
            return Response(
                {"message": "Post created successfully.", "post_id": post.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Write post failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeletePost(APIView):
    def delete(self, request):
        user_id_req = request.query_params.get("user_id")
        post_id_req = request.query_params.get("post_id")
        group_id_req = request.query_params.get("group_id")
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for deleting post {post_id_req} in group {group_id_req}.")
        
        user_id = user_id_req
        post_id = post_id_req
        group_id = group_id_req

        # Validate inputs
        try:
            user = User.objects.get(id=user_id)
            group = Group.objects.get(id=group_id)
            post = Post.objects.get(id=post_id)
        except User.DoesNotExist:
            logger.warning(f"Delete post failed for user {user_id_req} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            logger.warning(f"Delete post failed for user {user_id_req} to {path}: Group not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        except Post.DoesNotExist:
            logger.warning(f"Delete post failed for user {user_id_req} to {path}: Post not found.")
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a member of the group
        user_group = UserGroup.objects.filter(user=user, group=group).first()
        if not user_group:
            logger.warning(f"Delete post failed for user {user_id_req} to {path}: Not a member of group {group_id_req}.")
            return Response(
                {"error": "You are not a member of this group."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if the user is the post owner or an admin
        user_post = UserPost.objects.filter(user=user, post=post, group=group).first()
        is_admin = user_group.is_admin

        if not (user_post or is_admin):
            logger.warning(f"Delete post failed for user {user_id_req} to {path}: Unauthorized to delete post {post_id_req}.")
            return Response(
                {"error": "You are not authorized to delete this post."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Delete the post
            post.delete()
            logger.info(f"Post {post_id_req} deleted successfully by user {user_id_req} to {path}.")
            return Response(
                {"message": "Post deleted successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Delete post failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LikePost(APIView):
    def post(self, request):
        user_id_req = request.data.get("user_id")
        post_id_req = request.data.get("post_id")
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for liking post {post_id_req}.")
        
        user_id = user_id_req
        post_id = post_id_req

        # Validate inputs
        try:
            user = User.objects.get(id=user_id)
            post = Post.objects.get(id=post_id)
        except User.DoesNotExist:
            logger.warning(f"Like post failed for user {user_id_req} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Post.DoesNotExist:
            logger.warning(f"Like post failed for user {user_id_req} to {path}: Post not found.")
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the post belongs to a group
        try:
            user_post = UserPost.objects.get(
                post=post
            )  # Get the group associated with the post
            group = user_post.group
        except UserPost.DoesNotExist:
            logger.warning(f"Like post failed for user {user_id_req} to {path}: Post {post_id_req} does not belong to any group.")
            return Response(
                {"error": "This post does not belong to any group."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the user is a member of the group
        if not UserGroup.objects.filter(user=user, group=group, is_blocked=False).exists():
            logger.warning(f"Like post failed for user {user_id_req} to {path}: Not a member of the post's group.")
            return Response(
                {"error": "You are not a member of the group where this post was made."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if the user has already reacted to the post
        if UserReact.objects.filter(user=user, post=post).exists():
            logger.warning(f"Like post failed for user {user_id_req} to {path}: Already liked post {post_id_req}.")
            return Response(
                {"error": "You have already liked this post."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Create the reaction
            UserReact.objects.create(user=user, post=post)

            # Increment the reaction count for the post
            post.reaction_no += 1
            post.save()
            logger.info(f"Post {post_id_req} liked successfully by user {user_id_req} to {path}.")
            return Response({"message": "Post liked successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Like post failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UnlikePost(APIView):
    def post(self, request):
        user_id_req = request.data.get("user_id")
        post_id_req = request.data.get("post_id")
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for unliking post {post_id_req}.")
        
        user_id = user_id_req
        post_id = post_id_req

        # Validate inputs
        try:
            user = User.objects.get(id=user_id)
            post = Post.objects.get(id=post_id)
        except User.DoesNotExist:
            logger.warning(f"Unlike post failed for user {user_id_req} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Post.DoesNotExist:
            logger.warning(f"Unlike post failed for user {user_id_req} to {path}: Post not found.")
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user has already reacted to the post
        reaction = UserReact.objects.filter(user=user, post=post).first()
        if not reaction:
            logger.warning(f"Unlike post failed for user {user_id_req} to {path}: Not liked post {post_id_req}.")
            return Response(
                {"error": "You have not liked this post."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Delete the reaction
            reaction.delete()

            # Decrement the reaction count for the post
            post.reaction_no -= 1
            post.save()
            logger.info(f"Post {post_id_req} unliked successfully by user {user_id_req} to {path}.")
            return Response(
                {"message": "Post unliked successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Unlike post failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommentOnPost(APIView):
    def post(self, request):
        user_id_req = request.data.get("user_id")
        post_id_req = request.data.get("post_id")
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for commenting on post {post_id_req}.")
        
        serializer = CommentPostSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Comment on post failed for user {user_id_req} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data["user_id"]
        post_id = serializer.validated_data["post_id"]
        content = serializer.validated_data["content"]

        # Validate user and post
        try:
            user = User.objects.get(id=user_id)
            post = Post.objects.get(id=post_id)
        except User.DoesNotExist:
            logger.warning(f"Comment on post failed for user {user_id_req} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Post.DoesNotExist:
            logger.warning(f"Comment on post failed for user {user_id_req} to {path}: Post not found.")
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            user_post = UserPost.objects.get(
                post=post
            )  # Get the group associated with the post
            group = user_post.group
        except UserPost.DoesNotExist:
            logger.warning(f"Comment on post failed for user {user_id_req} to {path}: Post {post_id_req} does not belong to any group.")
            return Response(
                {"error": "This post does not belong to any group."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not UserGroup.objects.filter(user=user, group=group, is_blocked=False).exists():
            logger.warning(f"Comment on post failed for user {user_id_req} to {path}: Not a member of the post's group.")
            return Response(
                {"error": "You are not a member of the group where this post was made."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            # Create the comment
            comment = UserComment.objects.create(user=user, post=post, content=content)

            # Increment the comment count for the post
            post.comment_no += 1
            post.save()
            logger.info(f"Comment added successfully by user {user_id_req} on post {post_id_req} to {path}.")
            return Response(
                {"message": "Comment added successfully.", "comment_id": comment.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Comment on post failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteComment(APIView):
    def delete(self, request):
        user_id_req = request.query_params.get("user_id")
        comment_id_req = request.query_params.get("comment_id")
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for deleting comment {comment_id_req}.")
        
        user_id = user_id_req
        comment_id = comment_id_req

        # Validate inputs
        try:
            user = User.objects.get(id=user_id)
            comment = UserComment.objects.get(id=comment_id)
        except User.DoesNotExist:
            logger.warning(f"Delete comment failed for user {user_id_req} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except UserComment.DoesNotExist:
            logger.warning(f"Delete comment failed for user {user_id_req} to {path}: Comment {comment_id_req} not found.")
            return Response(
                {"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Ensure the user owns the comment
        if comment.user != user:
            logger.warning(f"Delete comment failed for user {user_id_req} to {path}: Unauthorized to delete comment {comment_id_req}.")
            return Response(
                {"error": "You are not authorized to delete this comment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Decrement the comment count for the post
            post = comment.post
            post.comment_no -= 1
            post.save()

            # Delete the comment
            comment.delete()
            logger.info(f"Comment {comment_id_req} deleted successfully by user {user_id_req} to {path}.")
            return Response(
                {"message": "Comment deleted successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Delete comment failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EditComment(APIView):
    def put(self, request):
        user_id_req = request.data.get("user_id")
        comment_id_req = request.data.get("comment_id")
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for editing comment {comment_id_req}.")
        
        serializer = EditCommentSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Edit comment failed for user {user_id_req} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data["user_id"]
        comment_id = serializer.validated_data["comment_id"]
        new_content = serializer.validated_data["content"]

        # Validate inputs
        try:
            user = User.objects.get(id=user_id)
            comment = UserComment.objects.get(id=comment_id)
        except User.DoesNotExist:
            logger.warning(f"Edit comment failed for user {user_id_req} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except UserComment.DoesNotExist:
            logger.warning(f"Edit comment failed for user {user_id_req} to {path}: Comment {comment_id_req} not found.")
            return Response(
                {"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Ensure the user owns the comment
        if comment.user != user:
            logger.warning(f"Edit comment failed for user {user_id_req} to {path}: Unauthorized to edit comment {comment_id_req}.")
            return Response(
                {"error": "You are not authorized to edit this comment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Update the comment content
            comment.content = new_content
            comment.save()
            logger.info(f"Comment {comment_id_req} updated successfully by user {user_id_req} to {path}.")
            return Response(
                {"message": "Comment updated successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Edit comment failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetGroupPosts(APIView):
    def get(self, request, group_id):
        user_id_req = request.user.id if request.user.is_authenticated else 'anonymous'
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for getting posts in group {group_id}.")
        
        # Validate the group exists
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            logger.warning(f"Get group posts failed for user {user_id_req} to {path}: Group {group_id} not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Fetch all posts in the group
            posts = Post.objects.filter(userpost__group=group).order_by(
                "-id"
            )  # Latest posts first

            # Serialize the data
            post_data = []
            for post in posts:
                comments = UserComment.objects.filter(post=post).order_by("add_date")
                reactions = UserReact.objects.filter(post=post).count()

                post_info = {
                    "post_id": post.id,
                    "content": post.content,
                    "reaction_no": reactions,
                    "comment_no": post.comment_no,
                    "comments": [
                        {
                            "comment_id": comment.id,
                            "username": comment.user.username,
                            "content": comment.content,
                            "add_date": comment.add_date,
                        }
                        for comment in comments
                    ],
                }
                post_data.append(post_info)
            logger.info(f"Group posts retrieved successfully by user {user_id_req} to {path} for group {group_id}.")
            return Response({"posts": post_data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Get group posts failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetUserGroupPosts(APIView):
    def get(self, request, user_id):
        user_id_req = user_id
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for getting user group posts.")
        
        # Validate the user exists
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.warning(f"Get user group posts failed for user {user_id_req} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Fetch all groups the user is a member of (and not blocked)
            user_groups = UserGroup.objects.filter(user=user, is_blocked=False).values_list(
                "group", flat=True
            )

            # Fetch all posts in those groups
            posts = Post.objects.filter(userpost__group__in=user_groups).order_by(
                "-id"
            )  # Latest posts first

            # Serialize the data
            post_data = []
            for post in posts:
                # Get the group associated with the post
                try:
                    user_post = UserPost.objects.get(post=post)
                    group_name = user_post.group.name
                except UserPost.DoesNotExist:
                    group_name = None  # In case the post is not linked to any group

                comments = UserComment.objects.filter(post=post).order_by("add_date")
                reactions = UserReact.objects.filter(post=post).count()

                post_info = {
                    "post_id": post.id,
                    "content": post.content,
                    "reaction_no": reactions,
                    "comment_no": post.comment_no,
                    "group_name": group_name,  # Include the group name here
                    "comments": [
                        {
                            "comment_id": comment.id,
                            "username": comment.user.username,
                            "content": comment.content,
                            "add_date": comment.add_date,
                        }
                        for comment in comments
                    ],
                }
                post_data.append(post_info)
            logger.info(f"User group posts retrieved successfully by user {user_id_req} to {path}.")
            return Response({"posts": post_data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Get user group posts failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LeaveGroup(APIView):
    def post(self, request):
        user_id_req = request.data.get("user_id")
        group_id_req = request.data.get("group_id")
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for leaving group {group_id_req}.")
        
        user_id = user_id_req
        group_id = group_id_req

        # Validate inputs
        try:
            user = User.objects.get(id=user_id)
            group = Group.objects.get(id=group_id)
        except User.DoesNotExist:
            logger.warning(f"Leave group failed for user {user_id_req} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            logger.warning(f"Leave group failed for user {user_id_req} to {path}: Group not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a member of the group
        user_group = UserGroup.objects.filter(user=user, group=group).first()
        if not user_group:
            logger.warning(f"Leave group failed for user {user_id_req} to {path}: Not a member of group {group_id_req}.")
            return Response(
                {"error": "You are not a member of this group."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent admins from leaving their own group
        if user_group.is_admin:
            logger.warning(f"Leave group failed for user {user_id_req} to {path}: Admin cannot leave own group.")
            return Response(
                {
                    "error": "Admins cannot leave their own group. Transfer ownership or delete the group."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Remove the user from the group
            user_group.delete()
            logger.info(f"User {user_id_req} successfully left group {group_id_req} to {path}.")
            return Response(
                {"message": "You have successfully left the group."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Leave group failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
