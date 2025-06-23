"""User views module for handling user-related API endpoints.

This module contains the UserViewSet class and related permission classes for managing
user operations like registration, authentication, profile management etc. It provides
endpoints for user CRUD operations with appropriate permission controls.

The module uses JWT authentication and implements role-based access control through
custom permission classes for staff and superuser operations.
"""

import logging
import threading

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.decorators import action, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken

from APIs.models.user_model import User
from APIs.serializers.user_serializers import (
    EmailTokenObtainPairSerializer,
    RegisterUserSerializer,
    ResendVerificationEmailSerializer,
    VerifyEmailSerializer,
)
from APIs.tasks import create_user_suggestions, send_verification_email


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
    - User registration and email verification
    - User authentication and token management
    - User profile retrieval and updates
    - User deletion and listing (admin only)

    Authentication is handled via JWT tokens. Different endpoints have different
    permission requirements ranging from AllowAny to IsAuthenticated to IsSuperUser.
    """

    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        """
        Determines the permissions required for each action.

        - 'create_user', 'verify', 'login', 'refresh_token', 'resend_verification_email': No authentication required.
        - 'all_users', 'create_superuser': Only superusers can access.
        - 'create_staff': Staff or superusers can access.
        - 'retrieve', 'update', 'destroy', 'change_password':
            - If a 'pk' (user ID) is provided in the URL, it's an admin action, requiring superuser permissions.
            - If no 'pk' is provided, it's a self-service action for the authenticated user.
        - Other actions: Require authentication.
        """
        if self.action in [
            "create_user",
            "verify",
            "login",
            "refresh_token",
            "resend_verification_email",
        ]:
            return [AllowAny()]
        elif self.action in ["all_users", "create_superuser"]:
            return [IsSuperUser()]
        elif self.action == "create_staff":
            return [IsStaffOrSuperUser()]
        elif self.action in ["retrieve", "update", "destroy", "change_password"]:
            if self.kwargs.get('pk'):
                return [IsSuperUser()]
            else:
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
        return Response(response_data, status=status_code)

    @swagger_auto_schema(
        operation_description="Register a new user",
        request_body=RegisterUserSerializer,
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=RegisterUserSerializer,
            ),
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def create_user(self, request):
        """
        Registers a new normal user.

        Ensures that no admin privileges are set during registration.
        Sends a verification email upon successful registration.
        """
        try:
            serializer = RegisterUserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return self._success_response(
                    message="Registration successful. Please check your email for verification.",
                    status_code=status.HTTP_201_CREATED,
                )
            return self._error_response(
                message="Registration failed", errors=serializer.errors
            )
        except IntegrityError as e:
            error_message = str(e)
            if "email" in error_message.lower():
                return self._error_response(
                    message="A user with this email already exists.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            elif "username" in error_message.lower():
                return self._error_response(
                    message="A user with this username already exists.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return self._error_response(
                    message=f"Registration failed: {error_message}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        except (RuntimeError, ValueError, AttributeError) as e:
            logging.error(f"Error in registration: {str(e)}", exc_info=True)
            return self._error_response(
                message="An error occurred during registration.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Verify user email with verification code (returns JWT tokens)",
        request_body=VerifyEmailSerializer,
        responses={
            200: "Email verified successfully",
            400: "Verification failed",
            500: "Internal Server Error",
        },
    )
    @action(detail=False, methods=["post"])
    def verify(self, request):
        """
        Verifies a user's email address using a verification code.
        Upon successful verification, generates and returns JWT tokens,
        and initiates asynchronous movie suggestion creation.
        """
        try:
            serializer = VerifyEmailSerializer(data=request.data)
            if not serializer.is_valid():
                return self._error_response(
                    message="Verification failed.",
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            validated_data = serializer.validated_data
            if not isinstance(validated_data, dict):
                return self._error_response(
                    message="Invalid validated data format from serializer.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            user = validated_data.get("user")
            key = validated_data.get("key")

            if not user or not key:
                return self._error_response(
                    message="Verification data missing.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            if not user.verify_email(key):
                return self._error_response(
                    message="Invalid verification key.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            threading.Thread(target=create_user_suggestions, args=(user.id,)).start()

            # Generate tokens directly for the user (no password required)
            refresh = RefreshToken.for_user(user)
            token_data = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
            }

            return self._success_response(
                data=token_data,
                message="Email verified successfully. You are now logged in.",
                status_code=status.HTTP_200_OK
            )

        except (
            ValidationError,
            ObjectDoesNotExist,
            ValueError,
            AttributeError,
        ) as e:
            logging.error(f"Error in verification: {str(e)}", exc_info=True)
            return self._error_response(
                message=f"Verification failed: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logging.error(f"Unexpected error in verification: {str(e)}", exc_info=True)
            return self._error_response(
                message=f"An unexpected error occurred during verification: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Login user and get JWT tokens",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, format="password"),
            },
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "status": openapi.Schema(type=openapi.TYPE_STRING),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "access": openapi.Schema(type=openapi.TYPE_STRING),
                                "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                                "user_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "username": openapi.Schema(type=openapi.TYPE_STRING),
                                "email": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                    },
                ),
            ),
            400: "Invalid input",
            401: "Invalid credentials",
            500: "Internal Server Error",
        },
    )
    @action(detail=False, methods=["post"])
    def login(self, request):
        """
        Authenticates a user and returns JWT access and refresh tokens.
        """
        logger = logging.getLogger(__name__)
        logger.info("Login view reached.")

        try:
            if not request.data.get("email") or not request.data.get("password"):
                return self._error_response(
                    message="Email and password are required.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            serializer = EmailTokenObtainPairSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            return self._success_response(data=data, message="Login successful.")
        except ValidationError as e:
            logger.error("Validation error in login: %s", e.detail)
            if isinstance(e.detail, dict):
                first_error_list = next(iter(e.detail.values()), ["An error occurred."])
                message = str(first_error_list[0])
            elif isinstance(e.detail, list):
                message = str(e.detail[0])
            else:
                message = str(e.detail)
            return self._error_response(
                message=message, status_code=status.HTTP_400_BAD_REQUEST
            )
        except TokenError:
            logger.error("Invalid credentials in login")
            return self._error_response(
                message="Invalid credentials.", status_code=status.HTTP_401_UNAUTHORIZED
            )
        except (RuntimeError, ValueError, AttributeError, ObjectDoesNotExist) as e:
            logger.error("Login error: %s", str(e), exc_info=True)
            return self._error_response(
                message="An unexpected error occurred during login.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Refresh JWT access token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={"refresh": openapi.Schema(type=openapi.TYPE_STRING)},
        ),
        responses={
            200: openapi.Response(
                description="Token refreshed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"access": openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
            401: "Invalid refresh token",
            500: "Internal Server Error",
        },
    )
    @action(detail=False, methods=["post"])
    def refresh_token(self, request):
        """
        Refreshes an expired JWT access token using a valid refresh token.
        """
        try:
            serializer = TokenRefreshSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            return self._success_response(
                data=serializer.validated_data, message="Token refreshed successfully."
            )
        except TokenError:
            return self._error_response(
                message="Invalid refresh token.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        except (RuntimeError, ValueError, AttributeError) as e:
            logger = logging.getLogger(__name__)
            logger.error("Error refreshing token: %s", str(e), exc_info=True)
            return self._error_response(
                message="An error occurred during token refresh.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Retrieve user details. For regular users, retrieves their own profile. For superusers, retrieves a user by ID.",
        security=[{"Bearer": []}],
        responses={
            200: RegisterUserSerializer,
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
            serializer = RegisterUserSerializer(target_user)
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
            },
        ),
        security=[{"Bearer": []}],
        responses={
            200: RegisterUserSerializer,
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

            if "is_staff" in request.data or "is_superuser" in request.data:
                if not request.user.is_superuser:
                    raise PermissionDenied("Insufficient permissions to modify admin status.")

            serializer = RegisterUserSerializer(target_user, data=request.data, partial=True)
            if serializer.is_valid():
                try:
                    serializer.save()
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

            if target_user.id == request.user.id and request.user.is_superuser:
                raise PermissionDenied("Superusers cannot delete their own account via this endpoint.")
            elif target_user.id != request.user.id and not request.user.is_superuser:
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
            serializer = RegisterUserSerializer(users, many=True)
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
            # Admin changing another user's password does not require old_password validation.

            target_user.password = make_password(new_password)
            target_user.save()
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
        operation_description="Resend verification email",
        request_body=ResendVerificationEmailSerializer,
        responses={
            200: "Verification email queued successfully",
            400: "Bad Request / Email already verified",
            404: "User not found",
            500: "Internal Server Error",
        },
    )
    @action(detail=False, methods=["post"])
    def resend_verification_email(self, request):
        """
        Resends a verification email to an unverified user.
        """
        try:
            serializer = ResendVerificationEmailSerializer(data=request.data)
            if not serializer.is_valid():
                return self._error_response(
                    message="Invalid request data.",
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            validated_data = serializer.validated_data
            if not isinstance(validated_data, dict):
                return self._error_response(
                    message="Invalid validated data format from serializer.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            email = validated_data.get("email")

            if not email:
                return self._error_response(
                    message="Email is required for resending verification.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            try:
                user = User.objects.get(email=email)
            except ObjectDoesNotExist:
                return self._error_response(
                    message="User not found.", status_code=status.HTTP_404_NOT_FOUND
                )

            auth_key = user.auth_key

            if not auth_key:
                return self._error_response(
                    message="No verification key found for this user. Please register again or contact support.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            logging.info(f"Sending re-verification email for {email}")
            threading.Thread(target=send_verification_email, args=[email, auth_key]).start()

            return self._success_response(
                message="Verification email sent successfully.",
                status_code=status.HTTP_200_OK,
            )

        except ValidationError as e:
            return self._error_response(
                message="Invalid data provided.",
                errors=e.detail,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except (RuntimeError, ValueError, AttributeError, ObjectDoesNotExist) as e:
            logging.error(f"Unexpected error in resend_verification_email: {str(e)}", exc_info=True)
            return self._error_response(
                message=f"An unexpected error occurred: {str(e)}",
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
        """
        Creates a new superuser. Only superusers can access this endpoint.
        """
        if not request.user.is_superuser:
            return self._error_response(
                message="Insufficient permissions.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            user.is_email_verified = True
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
        """
        Creates a new staff user. Only staff or superusers can access this endpoint.
        """
        if not (request.user.is_staff or request.user.is_superuser):
            return self._error_response(
                message="Insufficient permissions.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_staff = True
            user.is_active = True
            user.is_email_verified = True
            user.save()
            return self._success_response(
                data=RegisterUserSerializer(user).data,
                message="Staff user created successfully.",
                status_code=status.HTTP_201_CREATED,
            )
        return self._error_response(
            message="Staff user creation failed.", errors=serializer.errors
        )