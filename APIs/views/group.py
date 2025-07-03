import logging
from rest_framework import status, serializers # Import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated # Import IsAuthenticated
from rest_framework.pagination import PageNumberPagination # New import for pagination
from drf_yasg.utils import swagger_auto_schema # Import swagger_auto_schema
from drf_yasg.openapi import Parameter, IN_QUERY, IN_PATH, TYPE_INTEGER, TYPE_STRING, TYPE_BOOLEAN # Import for Swagger parameters
from drf_yasg import openapi # Import openapi
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
    BlockUserSerializer,
    UnblockUserSerializer,
    WritePostSerializer,
    CommentPostSerializer,
    EditCommentSerializer,
    EditPostSerializer,
    GroupSerializer, # New import
    EditGroupSerializer, # New import
)

logger = logging.getLogger(__name__)

class MyGroups(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_id="GetMyGroups",
        operation_description="Retrieve all groups that the authenticated user has joined, with an indicator of group ownership.",
        tags=["Groups"],
        responses={
            200: openapi.Response(
                description="Groups retrieved successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'groups': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=TYPE_INTEGER),
                                    'name': openapi.Schema(type=TYPE_STRING),
                                    'description': openapi.Schema(type=TYPE_STRING),
                                    'create_date': openapi.Schema(type=TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                    'is_owner': openapi.Schema(type=TYPE_BOOLEAN, description='True if the authenticated user created this group'),
                                }
                            )
                        )
                    }
                )
            ),
            500: "Internal Server Error",
        }
    )
    def get(self, request):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for getting my groups.")

        try:
            # Fetch all groups the user is a member of
            user_groups = UserGroup.objects.filter(user=user).select_related('group')

            group_data = []
            for user_group in user_groups:
                group = user_group.group
                is_owner = (group.usergroup_set.filter(user=user, is_admin=True).count() > 0)

                group_info = {
                    "id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "create_date": group.create_date,
                    "is_owner": is_owner,
                }
                group_data.append(group_info)
            logger.info(f"My groups retrieved successfully by user {user.id} to {path}.")
            return Response({"groups": group_data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Get my groups failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GroupPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class GetAllGroups(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_id="GetAllGroups",
        operation_description="Retrieve all groups, with optional filtering by group name or description. Supports pagination.",
        manual_parameters=[
            Parameter('search', IN_QUERY, type=TYPE_STRING, description='Search term for group name or description (optional)'),
            Parameter('page', IN_QUERY, type=TYPE_INTEGER, description='Page number (optional)'),
            Parameter('page_size', IN_QUERY, type=TYPE_INTEGER, description='Number of results per page (default: 10, max: 100)')
        ],
        tags=["Groups"],
        responses={
            200: openapi.Response(
                description="Groups retrieved successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=TYPE_INTEGER),
                        'next': openapi.Schema(type=TYPE_STRING, nullable=True),
                        'previous': openapi.Schema(type=TYPE_STRING, nullable=True),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=TYPE_INTEGER),
                                    'name': openapi.Schema(type=TYPE_STRING),
                                    'description': openapi.Schema(type=TYPE_STRING),
                                    'create_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                    'is_member': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='True if the authenticated user is a member of this group'),
                                }
                            )
                        )
                    }
                )
            ),
            500: "Internal Server Error",
        }
    )
    def get(self, request):
        user = request.user
        path = request.path
        search_query = request.query_params.get("search", None)
        logger.info(f"Request by user {user.id} to {path} for getting all groups with search query: {search_query}.")

        try:
            groups = Group.objects.all()
            if search_query:
                groups = groups.filter(name__icontains=search_query) | groups.filter(description__icontains=search_query)
            
            paginator = GroupPagination()
            paginated_groups = paginator.paginate_queryset(groups, request, view=self)
            serializer = GroupSerializer(paginated_groups, many=True, context={'request': request})
            logger.info(f"Groups retrieved successfully by user {user.id} to {path}.")
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            logger.error(f"Get all groups failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteGroup(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Delete a group (admin or superuser only).",
        manual_parameters=[
            Parameter('group_id', IN_PATH, type=TYPE_INTEGER, description='ID of the group to delete')
        ],
        tags=["Groups"],
        responses={
            200: "Group deleted successfully.",
            400: "Bad Request - Invalid data.",
            403: "Forbidden - Not authorized to delete this group.",
            404: "Group not found.",
            500: "Internal Server Error",
        }
    )
    def delete(self, request, group_id):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for deleting a group.")

        # group_id is now taken from URL path, no need for serializer validation for group_id
        # serializer = DeleteGroupSerializer(data=request.data)
        # if not serializer.is_valid():
        #     logger.warning(f"Delete group failed for user {user.id} to {path}: {serializer.errors}")
        #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # group_id = serializer.validated_data.get("group_id")

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            logger.warning(f"Delete group failed for user {user.id} to {path}: Group {group_id} not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a superuser or an admin of the group
        is_superuser = user.is_superuser
        is_group_admin = UserGroup.objects.filter(user=user, group=group, is_admin=True).exists()

        if not (is_superuser or is_group_admin):
            logger.warning(f"Delete group failed for user {user.id} to {path}: Unauthorized to delete group {group_id}.")
            return Response(
                {"error": "You are not authorized to delete this group."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            group.delete()
            logger.info(f"Group {group_id} deleted successfully by user {user.id} to {path}.")
            return Response(
                {"message": "Group deleted successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Delete group failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EditGroup(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Edit a group (admin or superuser only).",
        request_body=EditGroupSerializer,
        tags=["Groups"],
        responses={
            200: "Group updated successfully.",
            400: "Bad Request - Invalid data.",
            403: "Forbidden - Not authorized to edit this group.",
            404: "Group not found.",
            500: "Internal Server Error",
        }
    )
    def patch(self, request, group_id):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for editing group {group_id}.")

        serializer = EditGroupSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Edit group failed for user {user.id} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_name = serializer.validated_data.get("group_name")
        new_description = serializer.validated_data.get("description")

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            logger.warning(f"Edit group failed for user {user.id} to {path}: Group {group_id} not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a superuser or an admin of the group
        is_superuser = user.is_superuser
        is_group_admin = UserGroup.objects.filter(user=user, group=group, is_admin=True).exists()

        if not (is_superuser or is_group_admin):
            logger.warning(f"Edit group failed for user {user.id} to {path}: Unauthorized to edit group {group_id}.")
            return Response(
                {"error": "You are not authorized to edit this group."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            if new_name:
                group.name = new_name
            if new_description:
                group.description = new_description
            group.save()
            logger.info(f"Group {group_id} updated successfully by user {user.id} to {path}.")
            return Response(
                {"message": "Group updated successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Edit group failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateGroup(APIView):
    permission_classes = [IsAuthenticated] # Require authentication
    @swagger_auto_schema(
        operation_id="CreateGroup",
        operation_description="Create a new group and add the authenticated user as an admin.",
        request_body=CreateGroupSerializer, # Explicitly define request body for Swagger
        tags=["Groups"],
        responses={
            201: openapi.Response(
                description="Group created successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'group_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            400: "Bad Request - Invalid data",
            500: "Internal Server Error",
        }
    )
    def post(self, request):
        user = request.user # Get authenticated user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for creating a group.")
        
        serializer = CreateGroupSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Create group failed for user {user.id} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        group_name = serializer.validated_data["group_name"] # type: ignore
        description = serializer.validated_data["description"] # type: ignore
        
        try:
            # Create the group
            group = Group.objects.create(name=group_name, description=description)

            # Add the authenticated user to the group as an admin
            UserGroup.objects.create(user=user, group=group, is_admin=True, is_blocked=False)
            logger.info(f"Group '{group_name}' created successfully by user {user.id} to {path}.")
            return Response(
                {"message": "Group created successfully.", "group_id": group.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Create group failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JoinGroup(APIView):
    permission_classes = [IsAuthenticated] # Require authentication
    @swagger_auto_schema(
        operation_description="Join an existing group.",
        manual_parameters=[
            Parameter('group_id', IN_PATH, type=TYPE_INTEGER, description='ID of the group to join')
        ],
        tags=["Groups"],
        responses={
            201: "User joined the group successfully.",
            400: "Bad Request - Invalid data or already a member.",
            404: "Group not found.",
            500: "Internal Server Error",
        }
    )
    def post(self, request, group_id):
        user = request.user # Get authenticated user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for joining group {group_id}.")
        
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            logger.warning(f"Join group failed for user {user.id} to {path}: Group not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is already a member of the group
        if UserGroup.objects.filter(user=user, group=group).exists():
            logger.warning(f"Join group failed for user {user.id} to {path}: User already a member of group {group_id}.")
            return Response({"error": "You are already a member of this group."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Add the user to the group
            UserGroup.objects.create(user=user, group=group, is_admin=False, is_blocked=False)
            logger.info(f"User {user.id} joined group {group_id} successfully to {path}.")
            return Response(
                {"message": "User joined the group successfully."},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Join group failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BlockUser(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        request_body=BlockUserSerializer,
        tags=["Groups Users"],
        operation_description="Block a user within a specific group (admin only).",
        operation_summary="Block User in Group"
    )
    def post(self, request):
        admin_user = request.user
        path = request.path
        logger.info(f"Request by admin {admin_user.id} to {path} for blocking a user.")
        
        serializer = BlockUserSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Block user failed for admin {admin_user.id} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        group_id = serializer.validated_data["group_id"] # type: ignore
        blocked_user_id = serializer.validated_data["blocked_user_id"] # type: ignore

        try:
            # Check if the authenticated user is an admin of the group
            admin_user_group = UserGroup.objects.get(user=admin_user, group_id=group_id, is_admin=True)
        except UserGroup.DoesNotExist:
            logger.warning(f"Block user failed for admin {admin_user.id} to {path}: Not an admin of group {group_id}.")
            return Response({"error": "You are not an admin of this group."}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Get the UserGroup entry for the blocked user
            user_group = UserGroup.objects.get(user_id=blocked_user_id, group_id=group_id)

            # Block the user
            user_group.is_blocked = True
            user_group.save()
            logger.info(f"User {blocked_user_id} blocked successfully by admin {admin_user.id} in group {group_id} to {path}.")
            return Response(
                {"message": "User blocked successfully."}, status=status.HTTP_200_OK
            )
        except UserGroup.DoesNotExist:
            logger.warning(f"Block user failed for admin {admin_user.id} to {path}: User {blocked_user_id} not in group {group_id}.")
            return Response({"error": "User not found in this group."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Block user failed for admin {admin_user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetBlockedUsers(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        manual_parameters=[
            Parameter('group_id', IN_QUERY, type=TYPE_INTEGER, description='ID of the group')
        ],
        tags=["Groups Users"],
        operation_description="Retrieve a list of blocked users in a specific group (admin only).",
        operation_summary="Get Blocked Users in Group"
    )
    def get(self, request):
        admin_user = request.user
        path = request.path
        group_id = request.query_params.get("group_id")
        logger.info(f"Request by admin {admin_user.id} to {path} for getting blocked users in group {group_id}.")
        
        if not group_id:
            logger.warning(f"Get blocked users failed for admin {admin_user.id} to {path}: Group ID not provided.")
            return Response({"error": "Group ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate admin user and group
        try:
            admin = UserGroup.objects.get(
                user=admin_user, group_id=group_id, is_admin=True
            )
        except UserGroup.DoesNotExist:
            logger.warning(f"Get blocked users failed for admin {admin_user.id} to {path}: Not an admin of group {group_id}.")
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
            logger.info(f"Blocked users retrieved successfully by admin {admin_user.id} in group {group_id} to {path}.")
            return Response({"blocked_users": blocked_user_data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Get blocked users failed for admin {admin_user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UnblockUser(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        request_body=UnblockUserSerializer,
        tags=["Groups Users"],
        operation_description="Unblock a user within a specific group (admin only).",
        operation_summary="Unblock User in Group"
    )
    def post(self, request):
        admin_user = request.user
        path = request.path
        logger.info(f"Request by admin {admin_user.id} to {path} for unblocking a user.")
        
        serializer = UnblockUserSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Unblock user failed for admin {admin_user.id} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        group_id = serializer.validated_data["group_id"] # type: ignore
        unblocked_user_id = serializer.validated_data["unblocked_user_id"] # type: ignore

        try:
            # Check if the authenticated user is an admin of the group
            admin_user_group = UserGroup.objects.get(user=admin_user, group_id=group_id, is_admin=True)
        except UserGroup.DoesNotExist:
            logger.warning(f"Unblock user failed for admin {admin_user.id} to {path}: Not an admin of group {group_id}.")
            return Response({"error": "You are not an admin of this group."}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Get the UserGroup entry for the unblocked user
            user_group = UserGroup.objects.get(user_id=unblocked_user_id, group_id=group_id)

            # Unblock the user
            user_group.is_blocked = False
            user_group.save()
            logger.info(f"User {unblocked_user_id} unblocked successfully by admin {admin_user.id} in group {group_id} to {path}.")
            return Response(
                {"message": "User unblocked successfully."}, status=status.HTTP_200_OK
            )
        except UserGroup.DoesNotExist:
            logger.warning(f"Unblock user failed for admin {admin_user.id} to {path}: User {unblocked_user_id} not found in group {group_id}.")
            return Response({"error": "User not found in this group."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unblock user failed for admin {admin_user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WritePost(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        manual_parameters=[
            Parameter('group_id', IN_PATH, type=TYPE_INTEGER, description='ID of the group to create a post in')
        ],
        request_body=WritePostSerializer,
        tags=['Posts'],
        operation_description="Create a new post within a group.",
        operation_summary="Write Post"
    )
    def post(self, request, group_id):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for writing a post in group {group_id}.")
        
        serializer = WritePostSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Write post failed for user {user.id} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        content = serializer.validated_data["content"] # type: ignore

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            logger.warning(f"Write post failed for user {user.id} to {path}: Group not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a member of the group and not blocked
        if not UserGroup.objects.filter(user=user, group=group, is_blocked=False).exists():
            logger.warning(f"Write post failed for user {user.id} to {path}: Not a member of group {group_id}.")
            return Response(
                {"error": "You are not a member of this group or you are blocked."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Create the post
            post = Post.objects.create(content=content, reaction_no=0, comment_no=0)

            # Link the post to the user and group
            UserPost.objects.create(user=user, group=group, post=post)
            logger.info(f"Post created successfully by user {user.id} in group {group_id} to {path}.")
            return Response(
                {"message": "Post created successfully.", "post_id": post.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Write post failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeletePost(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Delete a post from a group (post owner, group admin, or superuser only).",
        manual_parameters=[
            Parameter('group_id', IN_PATH, type=TYPE_INTEGER, description='ID of the group the post belongs to'),
            Parameter('post_id', IN_PATH, type=TYPE_INTEGER, description='ID of the post to delete')
        ],
        tags=['Posts'],
        responses={
            200: "Post deleted successfully.",
            403: "Forbidden - Not authorized to delete this post.",
            404: "Group or Post not found.",
            500: "Internal Server Error",
        }
    )
    def delete(self, request, group_id, post_id):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for deleting post {post_id} from group {group_id}.")
        
        try:
            group = Group.objects.get(id=group_id)
            post = Post.objects.get(id=post_id)
        except Group.DoesNotExist:
            logger.warning(f"Delete post failed for user {user.id} to {path}: Group {group_id} not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        except Post.DoesNotExist:
            logger.warning(f"Delete post failed for user {user.id} to {path}: Post {post_id} not found.")
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a superuser
        is_superuser = user.is_superuser
        
        # Check if the user is the post owner
        is_post_owner = UserPost.objects.filter(user=user, post=post, group=group).exists()
        
        # Check if the user is an admin of the group
        is_group_admin = UserGroup.objects.filter(user=user, group=group, is_admin=True).exists()

        if not (is_superuser or is_post_owner or is_group_admin):
            logger.warning(f"Delete post failed for user {user.id} to {path}: Unauthorized to delete post {post_id}.")
            return Response(
                {"error": "You are not authorized to delete this post."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Delete the post
            post.delete()
            logger.info(f"Post {post_id} deleted successfully by user {user.id} to {path}.")
            return Response(
                {"message": "Post deleted successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Delete post failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LikePost(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        manual_parameters=[
            Parameter('group_id', IN_PATH, type=TYPE_INTEGER, description='ID of the group the post belongs to'),
            Parameter('post_id', IN_PATH, type=TYPE_INTEGER, description='ID of the post to like')
        ],
        tags=['Post Reacts'],
        operation_description="Like an existing post.",
        operation_summary="Like Post"
    )
    def post(self, request, group_id, post_id):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for liking post {post_id} in group {group_id}.")
        
        # Validate inputs
        try:
            group = Group.objects.get(id=group_id)
            post = Post.objects.get(id=post_id)
        except Group.DoesNotExist:
            logger.warning(f"Like post failed for user {user.id} to {path}: Group {group_id} not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        except Post.DoesNotExist:
            logger.warning(f"Like post failed for user {user.id} to {path}: Post {post_id} not found.")
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a member of the group
        if not UserGroup.objects.filter(user=user, group=group, is_blocked=False).exists():
            logger.warning(f"Like post failed for user {user.id} to {path}: Not a member of group {group_id}.")
            return Response(
                {"error": "You are not a member of this group."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if the user has already reacted to the post
        if UserReact.objects.filter(user=user, post=post).exists():
            logger.warning(f"Like post failed for user {user.id} to {path}: Already liked post {post_id}.")
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
            logger.info(f"Post {post_id} liked successfully by user {user.id} to {path}.")
            return Response({"message": "Post liked successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Like post failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UnlikePost(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        manual_parameters=[
            Parameter('group_id', IN_PATH, type=TYPE_INTEGER, description='ID of the group the post belongs to'),
            Parameter('post_id', IN_PATH, type=TYPE_INTEGER, description='ID of the post to unlike')
        ],
        tags=['Post Reacts'],
        operation_description="Unlike a previously liked post.",
        operation_summary="Unlike Post"
    )
    def post(self, request, group_id, post_id):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for unliking post {post_id} in group {group_id}.")
        
        # Validate inputs
        try:
            group = Group.objects.get(id=group_id)
            post = Post.objects.get(id=post_id)
        except Group.DoesNotExist:
            logger.warning(f"Unlike post failed for user {user.id} to {path}: Group {group_id} not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        except Post.DoesNotExist:
            logger.warning(f"Unlike post failed for user {user.id} to {path}: Post {post_id} not found.")
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a member of the group
        if not UserGroup.objects.filter(user=user, group=group, is_blocked=False).exists():
            logger.warning(f"Unlike post failed for user {user.id} to {path}: Not a member of group {group_id}.")
            return Response(
                {"error": "You are not a member of this group."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if the user has already reacted to the post
        reaction = UserReact.objects.filter(user=user, post=post).first()
        if not reaction:
            logger.warning(f"Unlike post failed for user {user.id} to {path}: Not liked post {post_id}.")
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
            logger.info(f"Post {post_id} unliked successfully by user {user.id} to {path}.")
            return Response(
                {"message": "Post unliked successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Unlike post failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommentOnPost(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        manual_parameters=[
            Parameter('group_id', IN_PATH, type=TYPE_INTEGER, description='ID of the group the post belongs to'),
            Parameter('post_id', IN_PATH, type=TYPE_INTEGER, description='ID of the post to comment on')
        ],
        request_body=CommentPostSerializer,
        tags=['Post Comments'],
        operation_description="Add a comment to an existing post.",
        operation_summary="Comment on Post"
    )
    def post(self, request, group_id, post_id):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for commenting on post {post_id} in group {group_id}.")
        
        serializer = CommentPostSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Comment on post failed for user {user.id} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        content = serializer.validated_data["content"] # type: ignore

        # Validate post
        try:
            group = Group.objects.get(id=group_id)
            post = Post.objects.get(id=post_id)
        except Group.DoesNotExist:
            logger.warning(f"Comment on post failed for user {user.id} to {path}: Group {group_id} not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        except Post.DoesNotExist:
            logger.warning(f"Comment on post failed for user {user.id} to {path}: Post not found.")
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            user_post = UserPost.objects.get(
                post=post
            )  # Get the group associated with the post
            group = user_post.group
        except UserPost.DoesNotExist:
            logger.warning(f"Comment on post failed for user {user.id} to {path}: Post {post_id} does not belong to any group.")
            return Response(
                {"error": "This post does not belong to any group."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not UserGroup.objects.filter(user=user, group=group, is_blocked=False).exists():
            logger.warning(f"Comment on post failed for user {user.id} to {path}: Not a member of the post's group.")
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
            logger.info(f"Comment added successfully by user {user.id} on post {post_id} to {path}.")
            return Response(
                {"message": "Comment added successfully.", "comment_id": comment.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Comment on post failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteComment(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        manual_parameters=[
            Parameter('group_id', IN_PATH, type=TYPE_INTEGER, description='ID of the group the post belongs to'),
            Parameter('post_id', IN_PATH, type=TYPE_INTEGER, description='ID of the post the comment belongs to'),
            Parameter('comment_id', IN_PATH, type=TYPE_INTEGER, description='ID of the comment to delete')
        ],
        tags=['Post Comments'],
        operation_description="Delete a comment from a post (comment owner or superuser only).",
        operation_summary="Delete Comment"
    )
    def delete(self, request, group_id, post_id, comment_id):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for deleting comment {comment_id} from post {post_id} in group {group_id}.")
        
        try:
            group = Group.objects.get(id=group_id) # Ensure group exists
            post = Post.objects.get(id=post_id) # Ensure post exists
            comment = UserComment.objects.get(id=comment_id)
        except Group.DoesNotExist:
            logger.warning(f"Delete comment failed for user {user.id} to {path}: Group {group_id} not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        except Post.DoesNotExist:
            logger.warning(f"Delete comment failed for user {user.id} to {path}: Post {post_id} not found.")
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)
        except UserComment.DoesNotExist:
            logger.warning(f"Delete comment failed for user {user.id} to {path}: Comment {comment_id} not found.")
            return Response(
                {"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if the user is a superuser
        is_superuser = user.is_superuser
        
        # Check if the user is the comment owner
        is_comment_owner = (comment.user == user)

        # Check if the user is the post owner
        is_post_owner = UserPost.objects.filter(user=user, post=post, group=group).exists()

        # Check if the user is an admin of the group
        is_group_admin = UserGroup.objects.filter(user=user, group=group, is_admin=True).exists()

        if not (is_superuser or is_comment_owner or is_post_owner or is_group_admin):
            logger.warning(f"Delete comment failed for user {user.id} to {path}: Unauthorized to delete comment {comment_id}.")
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
            logger.info(f"Comment {comment_id} deleted successfully by user {user.id} to {path}.")
            return Response(
                {"message": "Comment deleted successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Delete comment failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EditPost(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Edit the content of an existing post (post owner or superuser only).",
        manual_parameters=[
            Parameter('group_id', IN_PATH, type=TYPE_INTEGER, description='ID of the group the post belongs to'),
            Parameter('post_id', IN_PATH, type=TYPE_INTEGER, description='ID of the post to edit')
        ],
        request_body=EditPostSerializer,
        tags=['Posts'],
        responses={
            200: "Post updated successfully.",
            400: "Bad Request - Invalid data.",
            403: "Forbidden - Not authorized to edit this post.",
            404: "Post not found.",
            500: "Internal Server Error",
        }
    )
    def patch(self, request, group_id, post_id):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for editing post {post_id} in group {group_id}.")
        
        serializer = EditPostSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Edit post failed for user {user.id} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_content = serializer.validated_data["content"] # type: ignore

        try:
            group = Group.objects.get(id=group_id) # Ensure group exists
            post = Post.objects.get(id=post_id)
        except Group.DoesNotExist:
            logger.warning(f"Edit post failed for user {user.id} to {path}: Group {group_id} not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        except Post.DoesNotExist:
            logger.warning(f"Edit post failed for user {user.id} to {path}: Post {post_id} not found.")
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a superuser
        is_superuser = user.is_superuser
        
        # Check if the user is the post owner
        is_post_owner = UserPost.objects.filter(user=user, post=post).exists()

        if not (is_superuser or is_post_owner):
            logger.warning(f"Edit post failed for user {user.id} to {path}: Unauthorized to edit post {post_id}.")
            return Response(
                {"error": "You are not authorized to edit this post."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            post.content = new_content
            post.save()
            logger.info(f"Post {post_id} updated successfully by user {user.id} to {path}.")
            return Response(
                {"message": "Post updated successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Edit post failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EditComment(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        manual_parameters=[
            Parameter('group_id', IN_PATH, type=TYPE_INTEGER, description='ID of the group the post belongs to'),
            Parameter('post_id', IN_PATH, type=TYPE_INTEGER, description='ID of the post the comment belongs to'),
            Parameter('comment_id', IN_PATH, type=TYPE_INTEGER, description='ID of the comment to edit')
        ],
        request_body=EditCommentSerializer,
        tags=['Post Comments'],
        operation_description="Edit the content of an existing comment (comment owner or superuser only).",
        operation_summary="Edit Comment"
    )
    def patch(self, request, group_id, post_id, comment_id):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for editing comment {comment_id} from post {post_id} in group {group_id}.")
        
        serializer = EditCommentSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Edit comment failed for user {user.id} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_content = serializer.validated_data["content"] # type: ignore

        # Validate inputs
        try:
            group = Group.objects.get(id=group_id) # Ensure group exists
            post = Post.objects.get(id=post_id) # Ensure post exists
            comment = UserComment.objects.get(id=comment_id)
        except Group.DoesNotExist:
            logger.warning(f"Edit comment failed for user {user.id} to {path}: Group {group_id} not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        except Post.DoesNotExist:
            logger.warning(f"Edit comment failed for user {user.id} to {path}: Post {post_id} not found.")
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)
        except UserComment.DoesNotExist:
            logger.warning(f"Edit comment failed for user {user.id} to {path}: Comment {comment_id} not found.")
            return Response(
                {"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if the user is a superuser
        is_superuser = user.is_superuser
        
        # Ensure the user owns the comment
        is_comment_owner = (comment.user == user)

        if not (is_superuser or is_comment_owner):
            logger.warning(f"Edit comment failed for user {user.id} to {path}: Unauthorized to edit comment {comment_id}.")
            return Response(
                {"error": "You are not authorized to edit this comment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Update the comment content
            comment.content = new_content
            comment.save()
            logger.info(f"Comment {comment_id} updated successfully by user {user.id} to {path}.")
            return Response(
                {"message": "Comment updated successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Edit comment failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetGroupPosts(APIView):
    permission_classes = [IsAuthenticated] # Require authentication
    @swagger_auto_schema(
        operation_description="Retrieve posts from a specific group, accessible only if the user is a member or admin.",
        manual_parameters=[
            Parameter('group_id', IN_PATH, type=TYPE_INTEGER, description='ID of the group to retrieve posts from')
        ],
        tags=['Posts'],
        responses={
            200: openapi.Response(
                description="Posts retrieved successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'posts': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'post_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'content': openapi.Schema(type=openapi.TYPE_STRING),
                                    'reaction_no': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'comment_no': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'is_editable': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='True if the authenticated user can edit this post'),
                                }
                            )
                        )
                    }
                )
            ),
            403: "Forbidden - Not a member or admin of this group.",
            404: "Group not found.",
            500: "Internal Server Error",
        }
    )
    def get(self, request, group_id):
        user = request.user # Get authenticated user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for getting posts in group {group_id}.")
        
        # Validate the group exists
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            logger.warning(f"Get group posts failed for user {user.id} to {path}: Group {group_id} not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a member or admin of the group
        user_group_membership = UserGroup.objects.filter(user=user, group=group).first()
        if not user_group_membership:
            logger.warning(f"Get group posts failed for user {user.id} to {path}: Not a member or admin of group {group_id}.")
            return Response(
                {"error": "You are not a member or admin of this group."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Fetch all posts in the group
            posts = Post.objects.filter(userpost__group=group).order_by(
                "-id"
            )  # Latest posts first

            # Serialize the data
            post_data = []
            for post in posts:
                reactions = UserReact.objects.filter(post=post).count()

                # Determine if the current user can edit the post
                is_post_owner = UserPost.objects.filter(user=user, post=post).exists()

                is_editable = is_post_owner # Only the post owner can edit

                # Get the user who created the post
                user_post = UserPost.objects.filter(post=post).first()
                creator_id = user_post.user.id if user_post else None
                creator_username = user_post.user.username if user_post else None

                # Check if the user liked the post
                is_liked = UserReact.objects.filter(user=user, post=post).exists()

                post_info = {
                    "post_id": post.id,
                    "content": post.content,
                    "reaction_no": reactions,
                    "comment_no": post.comment_no,
                    "is_editable": is_editable,  # Add the is_editable flag
                    "user_id": creator_id,
                    "username": creator_username,
                    "is_liked": is_liked
                }
                post_data.append(post_info)
            logger.info(f"Group posts retrieved successfully by user {user.id} to {path} for group {group_id}.")
            return Response({
                "posts": post_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Get group posts failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetUserGroupPosts(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        manual_parameters=[
            Parameter('user_id', IN_PATH, type=TYPE_INTEGER, description='ID of the user to retrieve group posts for')
        ],
        tags=["Posts"],
        operation_description="Retrieve all posts made by a specific user across groups they are a member of.",
        operation_summary="Get User's Group Posts"
    )
    def get(self, request, user_id):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for getting user group posts.")
        
        # Validate the user exists
        try:
            # Ensure the requested user_id matches the authenticated user's ID
            if user.id != user_id:
                logger.warning(f"Get user group posts failed for user {user.id} to {path}: Unauthorized access to user {user_id}'s posts.")
                return Response({"error": "You are not authorized to view these posts."}, status=status.HTTP_403_FORBIDDEN)
            
            # No need to fetch user again if already authenticated and ID matches
            # user = User.objects.get(id=user_id) 
        except User.DoesNotExist: # This block might not be strictly necessary if IsAuthenticated ensures user exists
            logger.warning(f"Get user group posts failed for user {user.id} to {path}: User not found.")
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
                # Get the UserPost object to access user and group information
                try:
                    user_post = UserPost.objects.get(post=post)
                    group_name = user_post.group.name
                    creator_id = user_post.user.id
                    creator_username = user_post.user.username
                    is_owner = user_post.user == user
                except UserPost.DoesNotExist:
                    group_name = None
                    creator_id = None
                    creator_username = None
                    is_owner = False

                reactions = UserReact.objects.filter(post=post).count()
                is_liked = UserReact.objects.filter(user=user, post=post).exists()
                is_editable = is_owner

                post_info = {
                    "post_id": post.id,
                    "content": post.content,
                    "reaction_no": reactions,
                    "comment_no": post.comment_no,
                    "group_name": group_name,  # Include the group name here
                    "user_id": creator_id,
                    "username": creator_username,
                    "is_liked": is_liked,
                    "is_owner": is_owner,
                    "is_editable": is_editable,
                }
                post_data.append(post_info)
            logger.info(f"User group posts retrieved successfully by user {user.id} to {path}.")
            return Response({"posts": post_data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Get user group posts failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetAllCommentsForPost(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Retrieve all comments for a specific post within a group.",
        manual_parameters=[
            Parameter('group_id', IN_PATH, type=TYPE_INTEGER, description='ID of the group the post belongs to'),
            Parameter('post_id', IN_PATH, type=TYPE_INTEGER, description='ID of the post to retrieve comments for')
        ],
        tags=['Post Comments'],
        responses={
            200: openapi.Response(
                description="Comments retrieved successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'comments': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'comment_id': openapi.Schema(type=TYPE_INTEGER),
                                    'username': openapi.Schema(type=TYPE_STRING),
                                    'content': openapi.Schema(type=TYPE_STRING),
                                    'add_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                    'is_editable': openapi.Schema(type=TYPE_BOOLEAN, description='True if the authenticated user can edit this comment'),
                                }
                            )
                        )
                    }
                )
            ),
            403: "Forbidden - Not a member of the group.",
            404: "Group or Post not found.",
            500: "Internal Server Error",
        }
    )
    def get(self, request, group_id, post_id):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for getting comments for post {post_id} in group {group_id}.")

        try:
            group = Group.objects.get(id=group_id)
            post = Post.objects.get(id=post_id)
        except Group.DoesNotExist:
            logger.warning(f"Get comments failed for user {user.id} to {path}: Group {group_id} not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        except Post.DoesNotExist:
            logger.warning(f"Get comments failed for user {user.id} to {path}: Post {post_id} not found.")
            return Response({"error": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a member of the group
        if not UserGroup.objects.filter(user=user, group=group, is_blocked=False).exists():
            logger.warning(f"Get comments failed for user {user.id} to {path}: Not a member of group {group_id}.")
            return Response(
                {"error": "You are not a member of this group."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            comments = UserComment.objects.filter(post=post).order_by("add_date")
            comment_data = []
            for comment in comments:
                comment_info = {
                    "comment_id": comment.id,
                    "username": comment.user.username,
                    "user_id": comment.user.id,
                    "content": comment.content,
                    "add_date": comment.add_date,
                    "is_editable": (comment.user == user),
                }
                comment_data.append(comment_info)

            # Get post details
            user_post = UserPost.objects.filter(post=post).first()
            if user_post:
                group_name = user_post.group.name if user_post.group else None
            else:
                group_name = None

            # Determine if the current user can edit the post
            is_post_owner = UserPost.objects.filter(user=user, post=post).exists()
            is_superuser = user.is_superuser
            is_editable = is_post_owner or is_superuser

            # Get the user who created the post
            user_post = UserPost.objects.filter(post=post).first()
            if user_post:
                creator_id = user_post.user.id
                creator_username = user_post.user.username
            else:
                creator_id = None
                creator_username = None

            post_details = {
                "post_id": post.id,
                "content": post.content,
                "reaction_no": UserReact.objects.filter(post=post).count(),
                "comment_no": post.comment_no,
                "group_name": group_name,
                "is_editable": is_editable,
                "creator_id": creator_id,
                "creator_username": creator_username,
            }

            logger.info(f"Comments for post {post_id} retrieved successfully by user {user.id} to {path}.")
            return Response({"post": post_details, "comments": comment_data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Get comments failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LeaveGroup(APIView):
    permission_classes = [IsAuthenticated] # Require authentication
    @swagger_auto_schema(
        operation_description="Leave an existing group.",
        manual_parameters=[
            Parameter('group_id', IN_PATH, type=TYPE_INTEGER, description='ID of the group to leave')
        ],
        tags=["Groups"],
        responses={
            200: "You have successfully left the group.",
            400: "Bad Request - Not a member of this group.",
            403: "Forbidden - Admins cannot leave their own group.",
            404: "Group not found.",
            500: "Internal Server Error",
        }
    )
    def post(self, request, group_id):
        user = request.user # Get authenticated user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for leaving group {group_id}.")
        
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            logger.warning(f"Leave group failed for user {user.id} to {path}: Group {group_id} not found.")
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is a member of the group
        user_group = UserGroup.objects.filter(user=user, group=group).first()
        if not user_group:
            logger.warning(f"Leave group failed for user {user.id} to {path}: Not a member of group {group_id}.")
            return Response(
                {"error": "You are not a member of this group."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent admins from leaving their own group
        if user_group.is_admin:
            logger.warning(f"Leave group failed for user {user.id} to {path}: Admin cannot leave own group.")
            return Response(
                {
                    "error": "Admins cannot leave their own group. Transfer ownership or delete the group."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Remove the user from the group
            user_group.delete()
            logger.info(f"User {user.id} successfully left group {group_id} to {path}.")
            return Response(
                {"message": "You have successfully left the group."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Leave group failed for user {user.id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
