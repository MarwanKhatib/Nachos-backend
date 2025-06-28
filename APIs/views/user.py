"""User views module for handling user-related API endpoints.

This module contains the UserViewSet class and related permission classes for managing
user operations like profile management etc. It provides
endpoints for user CRUD operations with appropriate permission controls.

The module uses JWT authentication and implements role-based access control through
custom permission classes for staff and superuser operations.
"""

import logging

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.decorators import action, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404

from typing import cast

from APIs.models.user_model import User
from APIs.models.movie_model import Movie
from APIs.models.community_model import UserSuggestionList, UserMovieSuggestion, UserGenre # Import UserMovieSuggestion, UserGenre
from APIs.models.movie_genre_model import MovieGenre # Import MovieGenre
from APIs.serializers.user_serializers import RegisterUserSerializer, UserProfileSerializer
from APIs.serializers.movie_serializers import MovieSerializer
from APIs.utils.suggestion_helpers.genre_calculator import genres_delta # Import genres_delta


class IsSuperUser(permissions.BasePermission):
    """Permission class that allows access only to superuser accounts.

    This permission class checks if the requesting user has superuser privileges.
    It is used to restrict access to endpoints that should only be accessible
    by superusers/administrators.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsStaffOrSuperUser(permissions.BasePermission):
    """Permission class that allows access only to staff or superuser accounts.

    This permission class checks if the requesting user has either staff or superuser
    privileges. It is used to restrict access to endpoints that should only be
    accessible by administrators.
    """

    def has_permission(self, request, view):
        return request.user and (request.user.is_staff or request.user.is_superuser)


class UserViewSet(ViewSet):
    """ViewSet for handling user-related operations.

    This ViewSet provides endpoints for user management including:
    - User profile retrieval and updates
    - User deletion and listing (admin only)

    Authentication is handled via JWT tokens. Different endpoints have different
    permission requirements ranging from IsAuthenticated to IsSuperUser.
    """

    authentication_classes = [JWTAuthentication]
    logger = logging.getLogger(__name__)

    def get_permissions(self):
        """
        Determines the permissions required for each action.
        """
        if self.action in ["all_users", "create_superuser", "create_staff"]:
            return [IsSuperUser()]
        elif self.action in ["retrieve", "update", "destroy", "change_password", "upload_profile_picture"]:
            # If pk is provided, it's an admin action on another user, requires superuser
            if self.kwargs.get('pk'):
                return [IsSuperUser()]
            # If pk is not provided, it's a user managing their own profile, requires authentication
            else:
                return [IsAuthenticated()]
        elif self.action in ["get_suggestions"]:
            return [IsAuthenticated()]
        else:
            return [IsAuthenticated()]

    def _check_superuser_permission(self, request):
        """
        Checks if the requesting user has superuser privileges.

        Raises:
            PermissionDenied: If the user is not a superuser.
        """
        if not request.user.is_superuser:
            raise PermissionDenied("Insufficient permissions.")
        return True

    def _check_staff_permission(self, request):
        """
        Checks if the requesting user has staff or superuser privileges.

        Raises:
            PermissionDenied: If the user is neither staff nor superuser.
        """
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Insufficient permissions.")
        return True

    def _success_response(
        self, data=None, message=None, status_code=status.HTTP_200_OK
    ):
        """
        Standardized success response format.

        Args:
            data (dict, optional): The data to be returned. Defaults to None.
            message (str, optional): A success message. Defaults to None.
            status_code (int, optional): HTTP status code. Defaults to HTTP_200_OK.

        Returns:
            Response: A DRF Response object.
        """
        response_data = {"status": "success", "message": message, "data": data}
        return Response(response_data, status=status_code)

    def _error_response(
        self, message, errors=None, status_code=status.HTTP_400_BAD_REQUEST
    ):
        """
        Standardized error response format.

        Args:
            message (str): An error message.
            errors (dict, optional): A dictionary of validation errors. Defaults to None.
            status_code (int, optional): HTTP status code. Defaults to HTTP_400_BAD_REQUEST.

        Returns:
            Response: A DRF Response object.
        """
        response_data = {"status": "error", "message": message, "errors": errors}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Retrieve user details. For regular users, retrieves their own profile. For superusers, retrieves a user by ID.",
        security=[{"Bearer": []}],
        responses={
            200: UserProfileSerializer,
            401: "Unauthorized",
            403: "Permission denied",
            404: "User not found",
            500: "Internal Server Error",
        },
    )
    def retrieve(self, request, pk=None):
        """
        Retrieve user details. For regular users, retrieves their own profile. For superusers, retrieves a user by ID.
        """
        try:
            target_user = request.user
            if pk:
                if not request.user.is_superuser:
                    raise PermissionDenied("Insufficient permissions to retrieve other users.")
                target_user = get_object_or_404(User, pk=pk)
            elif not request.user.is_authenticated:
                raise PermissionDenied("User not authenticated.")
            
            # Use UserProfileSerializer for self-retrieval, RegisterUserSerializer for admin retrieval
            serializer = UserProfileSerializer(target_user) if not pk else RegisterUserSerializer(target_user)
            return self._success_response(
                data=serializer.data, message="User details retrieved successfully."
            )
        except ObjectDoesNotExist:
            return self._error_response(
                message="User not found.", status_code=status.HTTP_404_NOT_FOUND
            )
        except PermissionDenied as e:
            return self._error_response(
                message=str(e), status_code=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error retrieving user details: {e}", exc_info=True)
            return self._error_response(
                message="An error occurred while retrieving user details.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Retrieve a random selection of the top 10 personalized movie suggestions for the authenticated user.",
        operation_summary="Get top 10 movie suggestions",
        security=[{"Bearer": []}],
        responses={
            200: MovieSerializer(many=True),
            401: "Unauthorized",
            404: "No suggestions found",
            500: "Internal Server Error",
        },
        tags=["Users"],
    )
    @action(detail=False, methods=["get"], url_path="top-10-suggestions")
    def get_top_10_suggestions(self, request):
        """
        Retrieves a random selection of the top 10 personalized movie suggestions for the authenticated user.
        """
        user = request.user
        logger = logging.getLogger(__name__)
        logger.info(f"Attempting to retrieve top 10 suggestions for user: {user.id}")

        try:
            # Retrieve movie suggestions, ordered by 'total' score, excluding watched movies
            # Fetch a larger pool (e.g., top 50) to select 10 random ones from
            top_suggestions_pool = UserMovieSuggestion.objects.select_related('movie').filter( # type: ignore
                user=user,
                is_watched=False
            ).order_by('-total')[:50] # Take top 50 for randomness

            # Check if the queryset is empty or contains only zero-total suggestions
            if not top_suggestions_pool.exists() or all(s.total == 0 for s in top_suggestions_pool):
                logger.info(f"No meaningful top 10 suggestions found for user {user.id}. Attempting genre-based or random fallback.")
                
                user_genres = UserGenre.objects.filter(user=user).values_list('genre_id', flat=True) # type: ignore
                
                if user_genres.exists():
                    # If user has selected genres, suggest movies based on those genres
                    all_movies = Movie.objects.all().prefetch_related('moviegenre_set') # type: ignore
                    genre_based_suggestions = []
                    for movie in all_movies:
                        movie_genre_ids = [mg.genre_id for mg in movie.moviegenre_set.all()]
                        score = genres_delta(list(user_genres), movie_genre_ids)
                        if score > 0: # Only include movies with some genre match
                            genre_based_suggestions.append((score, movie))
                    
                    # Sort by score (descending) and take the top 10
                    genre_based_suggestions.sort(key=lambda x: x[0], reverse=True)
                    suggested_movies = [movie for score, movie in genre_based_suggestions][:10]

                    if not suggested_movies:
                        logger.info(f"No genre-based top 10 suggestions found for user {user.id}. Falling back to random.")
                        # Fallback to random if genre-based yields nothing
                        all_movies_fallback = list(Movie.objects.all()) # type: ignore
                        import random
                        random.shuffle(all_movies_fallback)
                        suggested_movies = all_movies_fallback[:10] # Default to 10 random
                else:
                    # If no genres selected, return random movies
                    logger.info(f"No genres selected for user {user.id}. Returning random top 10 movies.")
                    all_movies_fallback = list(Movie.objects.all()) # type: ignore
                    import random
                    random.shuffle(all_movies_fallback)
                    suggested_movies = all_movies_fallback[:10] # Default to 10 random
            else:
                # If queryset exists and has non-zero totals, use it
                import random
                num_suggestions_to_return = min(10, len(top_suggestions_pool))
                random_suggestions = random.sample(list(top_suggestions_pool), num_suggestions_to_return)
                suggested_movies = [ums.movie for ums in random_suggestions]

            serializer = MovieSerializer(suggested_movies, many=True)
            logger.info(f"Successfully retrieved {len(suggested_movies)} top suggestions for user {user.id}.")
            return self._success_response(
                data={
                    "count": len(suggested_movies), # This is the count of the actual suggestions returned (up to 10)
                    "results": serializer.data
                },
                message="Top 10 movie suggestions retrieved successfully.",
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error retrieving top 10 suggestions for user {user.id}: {e}", exc_info=True)
            return self._error_response(
                message="An error occurred while retrieving top 10 suggestions.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Retrieve personalized movie suggestions for the authenticated user. Supports pagination via an optional 'limit' query parameter.",
        operation_summary="Get user movie suggestions",
        security=[{"Bearer": []}],
        manual_parameters=[
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description="Optional: Limit the number of suggestions returned.",
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        responses={
            200: MovieSerializer(many=True),
            401: "Unauthorized",
            404: "No suggestions found",
            500: "Internal Server Error",
        },
        tags=["Users"],
    )
    @action(detail=False, methods=["get"])
    def get_suggestions(self, request):
        """
        Retrieves personalized movie suggestions for the authenticated user.
        Supports an optional 'limit' query parameter for pagination.
        """
        user = request.user
        logger = logging.getLogger(__name__)
        logger.info(f"Attempting to retrieve suggestions for user: {user.id}")

        try:
            limit = request.query_params.get('limit')
            
            # Base queryset for movie suggestions
            queryset = UserMovieSuggestion.objects.select_related('movie', 'movie__language').filter( # type: ignore
                user=user,
                is_watched=False # Exclude watched movies from suggestions
            ).order_by('-total')

            if limit:
                try:
                    limit = int(limit)
                    if limit <= 0:
                        raise ValueError("Limit must be a positive integer.")
                    queryset = queryset[:limit]
                except ValueError as e:
                    return self._error_response(
                        message=f"Invalid limit parameter: {e}",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

            # Check if the queryset is empty or contains only zero-total suggestions
            if not queryset.exists() or all(s.total == 0 for s in queryset):
                logger.info(f"No meaningful suggestions found for user {user.id}. Attempting genre-based or random fallback.")
                
                user_genres = UserGenre.objects.filter(user=user).values_list('genre_id', flat=True) # type: ignore
                
                if user_genres.exists():
                    # If user has selected genres, suggest movies based on those genres
                    all_movies = Movie.objects.all().prefetch_related('moviegenre_set') # type: ignore
                    genre_based_suggestions = []
                    for movie in all_movies:
                        movie_genre_ids = [mg.genre_id for mg in movie.moviegenre_set.all()]
                        score = genres_delta(list(user_genres), movie_genre_ids)
                        if score > 0: # Only include movies with some genre match
                            genre_based_suggestions.append((score, movie))
                    
                    # Sort by score (descending) and take the top ones
                    genre_based_suggestions.sort(key=lambda x: x[0], reverse=True)
                    suggested_movies = [movie for score, movie in genre_based_suggestions]
                    
                    if limit:
                        suggested_movies = suggested_movies[:limit]

                    if not suggested_movies:
                        logger.info(f"No genre-based suggestions found for user {user.id}. Falling back to random.")
                        # Fallback to random if genre-based yields nothing
                        all_movies_fallback = list(Movie.objects.all()) # type: ignore
                        import random
                        random.shuffle(all_movies_fallback)
                        suggested_movies = all_movies_fallback[:limit if limit else 10] # Default to 10 random if no limit
                else:
                    # If no genres selected, return random movies
                    logger.info(f"No genres selected for user {user.id}. Returning random movies.")
                    all_movies_fallback = list(Movie.objects.all()) # type: ignore
                    import random
                    random.shuffle(all_movies_fallback)
                    suggested_movies = all_movies_fallback[:limit if limit else 10] # Default to 10 random if no limit
            else:
                # If queryset exists and has non-zero totals, use it
                user_movie_suggestions = queryset
                suggested_movies = [ums.movie for ums in user_movie_suggestions]

            serializer = MovieSerializer(suggested_movies, many=True)
            logger.info(f"Successfully retrieved {len(suggested_movies)} suggestions for user {user.id}.")
            return self._success_response(
                data={
                    "count": len(suggested_movies), # Use len of actual suggested_movies
                    "results": serializer.data
                },
                message="Movie suggestions retrieved successfully.",
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error retrieving suggestions for user {user.id}: {e}", exc_info=True)
            return self._error_response(
                message="An error occurred while retrieving suggestions.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Update user information by ID (admin) or current authenticated user (regular user)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "user_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID of the user to update (admin only, overrides URL pk if present). This field is for admin use only and should not be sent by regular users.",
                    read_only=True,
                ),
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="User's email address"),
                "username": openapi.Schema(type=openapi.TYPE_STRING, description="User's username"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, format="password", write_only=True, description="User's password"),
                "birth_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", description="User's birth date (YYYY-MM-DD)"),
                "first_name": openapi.Schema(type=openapi.TYPE_STRING, description="User's first name"),
                "last_name": openapi.Schema(type=openapi.TYPE_STRING, description="User's last name"),
                "is_active": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="User account active status (admin only)"),
                "is_email_verified": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="User email verification status (admin only)"),
                "is_staff": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Staff status (superuser only)"),
                "is_superuser": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Superuser status (superuser only)"),
                "profile_picture": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY, description="User's profile picture (image file)"), # New field
            },
        ),
        security=[{"Bearer": []}],
        responses={
            200: UserProfileSerializer,
            401: "Unauthorized",
            403: "Permission denied",
            404: "User not found",
            500: "Internal Server Error",
        },
    )
    def update(self, request, pk=None):
        """
        Updates user information for a specific user.

        If `pk` is provided, updates the user with that ID (admin only).
        If `pk` is not provided, updates the authenticated user's profile.
        Only superusers can modify `is_staff` or `is_superuser` status.
        """
        try:
            target_user = request.user
            user_id_from_payload = request.data.get("user_id")

            if pk:
                if not request.user.is_superuser:
                    raise PermissionDenied("Insufficient permissions to update other users.")
                target_user = User.objects.get(pk=pk)
            elif user_id_from_payload is not None:
                if not request.user.is_superuser:
                    raise PermissionDenied("Insufficient permissions to update other users via payload ID.")
                target_user = User.objects.get(pk=user_id_from_payload)
            elif not request.user.is_authenticated:
                raise PermissionDenied("User not authenticated.")

            # Determine which serializer to use based on whether it's a self-update or admin update
            if pk or user_id_from_payload is not None: # Admin is updating another user
                if not request.user.is_superuser:
                    raise PermissionDenied("Insufficient permissions to update other users.")
                serializer = RegisterUserSerializer(target_user, data=request.data, partial=True)
            else: # User is updating their own profile
                serializer = UserProfileSerializer(target_user, data=request.data, partial=True)

            if serializer.is_valid():
                # Handle is_staff and is_superuser fields only if the request is from a superuser
                if request.user.is_superuser:
                    if "is_staff" in request.data:
                        target_user.is_staff = request.data["is_staff"]
                    if "is_superuser" in request.data:
                        target_user.is_superuser = request.data["is_superuser"]
                    if "is_active" in request.data:
                        target_user.is_active = request.data["is_active"]
                    if "is_email_verified" in request.data:
                        target_user.is_email_verified = request.data["is_email_verified"]
                elif "is_staff" in request.data or "is_superuser" in request.data or "is_active" in request.data or "is_email_verified" in request.data:
                    raise PermissionDenied("Insufficient permissions to modify admin/active/verified status.")

                try:
                    serializer.save()
                    target_user.save() # Save any changes made directly to target_user (e.g., is_staff, is_superuser)
                    return self._success_response(
                        data=serializer.data,
                        message="User information updated successfully.",
                    )
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error saving user {target_user.id}: {str(e)}", exc_info=True)
                    return self._error_response(
                        message=f"Error saving user: {str(e)}",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            else:
                logger = logging.getLogger(__name__)
                logger.error(f"Validation error for user {target_user.id}: {serializer.errors}")
                return self._error_response(
                    message="Update failed.", errors=serializer.errors
                )
        except ObjectDoesNotExist:
            return self._error_response(
                message="User not found.", status_code=status.HTTP_404_NOT_FOUND
            )
        except PermissionDenied as e:
            return self._error_response(
                message=str(e), status_code=status.HTTP_401_UNAUTHORIZED
            )
        except (RuntimeError, ValueError, AttributeError, IntegrityError) as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating user: {str(e)}", exc_info=True)
            return self._error_response(
                message=f"An error occurred: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Upload a profile picture for the authenticated user.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["profile_picture"],
            properties={
                "profile_picture": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_BINARY,
                    description="The profile picture file to upload.",
                ),
            },
        ),
        security=[{"Bearer": []}],
        responses={
            200: UserProfileSerializer,
            400: "Bad Request",
            401: "Unauthorized",
            500: "Internal Server Error",
        },
        tags=["Users"],
    )
    @action(detail=False, methods=["post"], url_path="upload-profile-picture")
    def upload_profile_picture(self, request):
        """
        Uploads a profile picture for the authenticated user.
        """
        user = request.user
        logger = logging.getLogger(__name__)
        logger.info(f"Attempting to upload profile picture for user: {user.id}")

        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                logger.info(f"Profile picture uploaded successfully for user {user.id}.")
                return self._success_response(
                    data=serializer.data,
                    message="Profile picture uploaded successfully.",
                    status_code=status.HTTP_200_OK,
                )
            except Exception as e:
                logger.error(f"Error saving profile picture for user {user.id}: {str(e)}", exc_info=True)
                return self._error_response(
                    message=f"Error uploading profile picture: {str(e)}",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            logger.error(f"Validation error for profile picture upload for user {user.id}: {serializer.errors}")
            return self._error_response(
                message="Profile picture upload failed.", errors=serializer.errors
            )

    @swagger_auto_schema(
        operation_description="Delete user",
        responses={
            204: "User deleted successfully",
            403: "Permission denied",
            404: "User not found",
            500: "Internal Server Error",
        },
    )
    def destroy(self, request, pk=None):
        """
        Deletes a user from the system.

        Allows an authenticated user to delete their own account (if no `pk` is provided).
        Allows a superuser to delete any user by ID (except themselves).
        """
        try:
            target_user = request.user
            if pk:
                if not request.user.is_superuser:
                    raise PermissionDenied("Insufficient permissions to delete other users.")
                target_user = User.objects.get(pk=pk)
            elif not request.user.is_authenticated:
                raise PermissionDenied("User not authenticated.")

            # A superuser can delete any user except themselves.
            # A normal user can only delete their own account.
            if pk: # Admin is deleting a specific user
                if not request.user.is_superuser:
                    raise PermissionDenied("Insufficient permissions to delete other users.")
                if target_user.id == request.user.id:
                    raise PermissionDenied("Superusers cannot delete their own account via this endpoint.")
            else: # User is deleting their own account
                if target_user.id != request.user.id: # This condition should ideally not be met if target_user is request.user
                    raise PermissionDenied("You can only delete your own account.")
                
            target_user.delete()
            return self._success_response(
                message="User deleted successfully.",
                status_code=status.HTTP_204_NO_CONTENT,
            )
        except ObjectDoesNotExist:
            return self._error_response(
                message="User not found.", status_code=status.HTTP_404_NOT_FOUND
            )
        except PermissionDenied as e:
            return self._error_response(
                message=str(e), status_code=status.HTTP_403_FORBIDDEN
            )
        except (RuntimeError, ValueError, AttributeError, IntegrityError) as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error deleting user: {str(e)}", exc_info=True)
            return self._error_response(
                message="An error occurred during deletion.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Get all users (superuser only)",
        responses={
            200: RegisterUserSerializer(many=True),
            403: "Permission denied",
            500: "Internal Server Error",
        },
    )
    @permission_classes([IsSuperUser])
    def all_users(self, request):
        """
        Retrieves a list of all users in the system.

        This endpoint is only accessible by superusers.
        """
        try:
            self._check_superuser_permission(request)

            users = User.objects.all()
            serializer = RegisterUserSerializer(users, many=True) # Use RegisterUserSerializer for admin list
            return self._success_response(
                data=serializer.data, message="Users retrieved successfully."
            )
        except PermissionDenied as e:
            return self._error_response(
                message=str(e), status_code=status.HTTP_403_FORBIDDEN
            )
        except (RuntimeError, ValueError, AttributeError, IntegrityError) as e:
            logging.error(f"Error retrieving all users: {str(e)}", exc_info=True)
            return self._error_response(
                message="An error occurred.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Change user password by ID (admin) or current authenticated user (regular user)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["old_password", "new_password"],
            properties={
                "old_password": openapi.Schema(
                    type=openapi.TYPE_STRING, format="password"
                ),
                "new_password": openapi.Schema(
                    type=openapi.TYPE_STRING, format="password"
                ),
            },
        ),
        security=[{"Bearer": []}],
        responses={
            200: "Password changed successfully",
            400: "Invalid input",
            401: "Unauthorized",
            403: "Permission denied",
            404: "User not found",
            500: "Internal Server Error",
        },
    )
    @action(detail=False, methods=["put"], url_path="change-password")
    def change_password(self, request, pk=None):
        """
        Changes the password for a user.

        If `pk` is provided, changes the password for that user (admin only).
        If `pk` is not provided, changes the password for the authenticated user.
        Requires `old_password` and `new_password` for self-service changes.
        Admin can change any user"s password without knowing the old one.
        """
        logger = logging.getLogger(__name__)
        target_user = request.user
        try:
            if pk:
                if not request.user.is_superuser:
                    raise PermissionDenied("Insufficient permissions to change other users' passwords.")
                target_user = User.objects.get(pk=pk)
            elif not request.user.is_authenticated:
                raise PermissionDenied("User not authenticated.")

            old_password = request.data.get("old_password")
            new_password = request.data.get("new_password")

            if not old_password or not new_password:
                raise ValidationError("Both old and new passwords are required.")

            if not request.user.is_superuser or (request.user.is_superuser and target_user.id == request.user.id):
                if not check_password(old_password, target_user.password):
                    raise ValidationError("Invalid old password.")

            target_user.password = make_password(new_password)
            logger.info(f"Attempting to save user {target_user.id} after password change.")
            target_user.save()
            logger.info(f"User {target_user.id} password saved successfully.")
            return self._success_response(message="Password changed successfully.")
        except ObjectDoesNotExist:
            return self._error_response(
                message="User not found.", status_code=status.HTTP_404_NOT_FOUND
            )
        except PermissionDenied as e:
            return self._error_response(
                message=str(e), status_code=status.HTTP_401_UNAUTHORIZED
            )
        except ValidationError as e:
            return self._error_response(
                message=str(e), status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            user_id_for_log = target_user.id if target_user else "N/A"
            logger.error(f"Error changing password for user {user_id_for_log}: {e}", exc_info=True)
            return self._error_response(
                message="An error occurred.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Create a new superuser (admin only)",
        request_body=RegisterUserSerializer,
        responses={
            201: openapi.Response(
                description="Superuser created successfully",
                schema=RegisterUserSerializer,
            ),
            400: "Bad Request",
            403: "Permission denied",
            500: "Internal Server Error",
        },
    )
    @action(detail=False, methods=["post"])
    def create_superuser(self, request):
        if not request.user.is_superuser:
            return self._error_response(
                message="Insufficient permissions.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user = cast(User, user)
            user.is_superuser = True # type: ignore
            user.is_staff = True # type: ignore
            user.is_active = True
            user.is_email_verified = True # Set to True as admin is creating it
            user.save()
            return self._success_response(
                data=RegisterUserSerializer(user).data,
                message="Superuser created successfully.",
                status_code=status.HTTP_201_CREATED,
            )
        return self._error_response(
            message="Superuser creation failed.", errors=serializer.errors
        )

    @swagger_auto_schema(
        operation_description="Create a new staff user (staff or superuser only)",
        request_body=RegisterUserSerializer,
        responses={
            201: openapi.Response(
                description="Staff user created successfully",
                schema=RegisterUserSerializer,
            ),
            400: "Bad Request",
            403: "Permission denied",
            500: "Internal Server Error",
        },
    )
    @action(detail=False, methods=["post"])
    def create_staff(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            return self._error_response(
                message="Insufficient permissions.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user = cast(User, user)
            user.is_staff = True # type: ignore
            user.is_active = True
            user.is_email_verified = True # Set to True as admin is creating it
            user.save()
            return self._success_response(
                data=RegisterUserSerializer(user).data,
                message="Staff user created successfully.",
                status_code=status.HTTP_201_CREATED,
            )
        return self._error_response(
            message="Staff user creation failed.", errors=serializer.errors
        )
