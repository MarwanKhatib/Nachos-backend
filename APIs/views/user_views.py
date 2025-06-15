"""User views module for handling user-related API endpoints.

This module contains the UserViewSet class and related permission classes for managing
user operations like registration, authentication, profile management etc. It provides
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
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from APIs.models.user_model import User
from APIs.serializers.user_serializers import (
    EmailTokenObtainPairSerializer,
    RegisterUserSerializer,
    ResendVerificationEmailSerializer,
    VerifyEmailSerializer,
)
from APIs.tasks import create_user_suggestions, test_celery


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
        if self.action in [
            "create_user",
            "verify",
            "login",
            "refresh_token",
            "test_celery",
            "resend_verification_email",
        ]:
            return [AllowAny()]  # No authentication needed for these endpoints
        elif self.action in ["all_users", "destroy", "create_superuser"]:
            return [IsSuperUser()]  # Only superuser can access these
        elif self.action in ["create_staff"]:
            return [IsStaffOrSuperUser()]  # Staff or superuser can access
        else:
            return [IsAuthenticated()]  # All other endpoints need authentication

    def _check_user_permission(self, request, user_id):
        """Check if user has permission to access/modify the resource"""
        if request.user.is_superuser:
            return True
        if request.user.is_staff:
            return True
        return request.user.id == user_id

    def _check_superuser_permission(self, request):
        """Check if user is superuser"""
        if not request.user.is_superuser:
            raise PermissionDenied("Insufficient permissions")
        return True

    def _check_staff_permission(self, request):
        """Check if user is staff or superuser"""
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Insufficient permissions")
        return True

    def _success_response(
        self, data=None, message=None, status_code=status.HTTP_200_OK
    ):
        """Standardized success response format"""
        response_data = {"status": "success", "message": message, "data": data}
        return Response(response_data, status=status_code)

    def _error_response(
        self, message, errors=None, status_code=status.HTTP_400_BAD_REQUEST
    ):
        """Standardized error response format"""
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
        """Create a normal user - no special permissions"""
        try:
            # Ensure no admin privileges are set
            request.data["is_staff"] = False
            request.data["is_superuser"] = False
            request.data["is_active"] = False
            request.data["is_email_verified"] = False

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
                    message="A user with this email already exists",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            elif "username" in error_message.lower():
                return self._error_response(
                    message="A user with this username already exists",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return self._error_response(
                    message=f"Registration failed: {error_message}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        except (RuntimeError, ValueError, AttributeError) as e:
            print(f"Error in registration: {str(e)}")
            return self._error_response(
                message="An error occurred during registration",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Verify user email with verification code",
        request_body=VerifyEmailSerializer,
        responses={
            200: "Email verified successfully",
            400: "Verification failed",
            500: "Internal Server Error",
        },
    )
    @action(detail=False, methods=["post"])
    def verify(self, request):
        """Verify user's email address using verification code.

        This endpoint verifies a user's email address by validating the verification code
        sent to their email during registration.

        Args:
            request: HTTP request object containing verification data (email and key)

        Returns:
            Response object with:
                - Success message if verification successful
                - Error message and appropriate status code on failure

        Raises:
            ValidationError: If verification data is invalid
            ObjectDoesNotExist: If user not found
            RuntimeError: If there's an error during verification
        """
        try:
            serializer = VerifyEmailSerializer(data=request.data)
            if not serializer.is_valid():
                return self._error_response(
                    message="Verification failed",
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            user = serializer.validated_data["user"]
            key = serializer.validated_data["key"]

            # Verify the email
            if not user.verify_email(key):
                return self._error_response(
                    message="Invalid verification key",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Create movie suggestions asynchronously
            create_user_suggestions.delay(user.id)

            return self._success_response(
                message="Email verified successfully", status_code=status.HTTP_200_OK
            )

        except (
            ValidationError,
            ObjectDoesNotExist,
            RuntimeError,
            ValueError,
            AttributeError,
        ) as e:
            print(f"Error in verification: {str(e)}")
            return self._error_response(
                message=f"An error occurred during verification: {str(e)}",
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
        """Login user and get JWT tokens"""
        logger = logging.getLogger(__name__)
        logger.info("Login view reached.")

        try:
            # Validate required fields
            if not request.data.get("email") or not request.data.get("password"):
                return self._error_response(
                    message="Email and password are required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            serializer = EmailTokenObtainPairSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            return self._success_response(data=data, message="Login successful")
        except ValidationError as e:
            logger.error("Validation error in login: %s", str(e))
            return self._error_response(
                message=str(e), status_code=status.HTTP_400_BAD_REQUEST
            )
        except TokenError:
            logger.error("Invalid credentials in login")
            return self._error_response(
                message="Invalid credentials", status_code=status.HTTP_401_UNAUTHORIZED
            )
        except (RuntimeError, ValueError, AttributeError, ObjectDoesNotExist):
            logger.error("Login error: %s", str(e))
            return self._error_response(
                message="An error occurred during login",
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
        """Refresh an expired JWT access token using a valid refresh token.

        This endpoint allows users to obtain a new access token by providing a valid refresh token.
        The refresh token must not be expired or invalidated.

        Args:
            request: HTTP request object containing the refresh token in request.data

        Returns:
            Response object with:
                - New access token on success
                - Error message and appropriate status code on failure

        Raises:
            TokenError: If refresh token is invalid or expired
            ValidationError: If request data is invalid
            RuntimeError: If there's an error during token refresh
        """
        try:
            serializer = TokenRefreshSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            return self._success_response(
                data=serializer.validated_data, message="Token refreshed successfully"
            )
        except TokenError:
            return self._error_response(
                message="Invalid refresh token",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        except (RuntimeError, ValueError, AttributeError) as e:
            logger = logging.getLogger(__name__)
            logger.error("Error refreshing token: %s", str(e))
            return self._error_response(
                message="An error occurred during token refresh",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Get user details",
        responses={
            200: RegisterUserSerializer,
            403: "Permission denied",
            404: "User not found",
            500: "Internal Server Error",
        },
    )
    def retrieve(self, request, pk=None):
        """Retrieve details for a specific user.

        Args:
            request: The HTTP request object containing user authentication details
            pk: Primary key (ID) of the user to retrieve

        Returns:
            Response object with:
                - User data and success message if found
                - Error message and appropriate status code on failure

        Raises:
            PermissionDenied: If user doesn't have permission to access the data
            ObjectDoesNotExist: If specified user not found
            RuntimeError: If there's an error retrieving the data
        """
        try:
            if not self._check_user_permission(request, pk):
                raise PermissionDenied("Insufficient permissions")

            user = User.objects.get(pk=pk)
            serializer = RegisterUserSerializer(user)
            return self._success_response(
                data=serializer.data, message="User details retrieved successfully"
            )
        except ObjectDoesNotExist:
            return self._error_response(
                message="User not found", status_code=status.HTTP_404_NOT_FOUND
            )
        except PermissionDenied as e:
            return self._error_response(
                message=str(e), status_code=status.HTTP_403_FORBIDDEN
            )
        except (RuntimeError, ValueError, AttributeError):
            return self._error_response(
                message="An error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Update user information",
        request_body=RegisterUserSerializer,
        responses={
            200: RegisterUserSerializer,
            403: "Permission denied",
            404: "User not found",
            500: "Internal Server Error",
        },
    )
    def update_user_info(self, request, pk=None):
        """Update user information.

        Args:
            request: HTTP request object containing user data to update
            pk: Primary key of the user to update

        Returns:
            Response object with:
                - Updated user data and success message on success
                - Error message and appropriate status code on failure

        Raises:
            PermissionDenied: If user doesn't have permission to update
            ObjectDoesNotExist: If specified user not found
            ValidationError: If update data is invalid
            RuntimeError: If there's an error during update
        """
        try:
            if not self._check_user_permission(request, pk):
                raise PermissionDenied("Insufficient permissions")

            user = User.objects.get(pk=pk)

            # Only superuser can modify admin status
            if not self._check_superuser_permission(request):
                if "is_staff" in request.data or "is_superuser" in request.data:
                    raise PermissionDenied("Insufficient permissions")

            serializer = RegisterUserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return self._success_response(
                    data=serializer.data,
                    message="User information updated successfully",
                )
            return self._error_response(
                message="Update failed", errors=serializer.errors
            )
        except ObjectDoesNotExist:
            return self._error_response(
                message="User not found", status_code=status.HTTP_404_NOT_FOUND
            )
        except PermissionDenied as e:
            return self._error_response(
                message=str(e), status_code=status.HTTP_403_FORBIDDEN
            )
        except (RuntimeError, ValueError, AttributeError, IntegrityError):
            return self._error_response(
                message="An error occurred",
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
        """Delete a user from the system.

        This endpoint is only accessible by superusers and allows deletion of any user
        except the requesting superuser themselves.

        Args:
            request: The HTTP request object containing user authentication details
            pk: Primary key (ID) of the user to be deleted

        Returns:
            Response object with:
                - Success message and 204 status on successful deletion
                - Error message and appropriate status code on failure

        Raises:
            PermissionDenied: If user is not a superuser or tries to delete themselves
            ObjectDoesNotExist: If specified user does not exist
            RuntimeError: If there's an error during deletion
        """
        try:
            if not self._check_superuser_permission(request):
                raise PermissionDenied("Insufficient permissions")

            user = User.objects.get(pk=pk)

            # Prevent self-deletion
            if user.id == request.user.id:
                raise PermissionDenied("Cannot delete your own account")

            user.delete()
            return self._success_response(
                message="User deleted successfully",
                status_code=status.HTTP_204_NO_CONTENT,
            )
        except ObjectDoesNotExist:
            return self._error_response(
                message="User not found", status_code=status.HTTP_404_NOT_FOUND
            )
        except PermissionDenied as e:
            return self._error_response(
                message=str(e), status_code=status.HTTP_403_FORBIDDEN
            )
        except (RuntimeError, ValueError, AttributeError, IntegrityError):
            return self._error_response(
                message="An error occurred",
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
        """Get a list of all users in the system.

        This endpoint is only accessible by superusers and returns details of all registered users.

        Args:
            request: The HTTP request object containing user authentication details

        Returns:
            Response object with:
                - List of serialized user data on success
                - Error message and status code on failure

        Raises:
            PermissionDenied: If user is not a superuser
            RuntimeError: If there's an error retrieving users
        """
        try:
            if not self._check_superuser_permission(request):
                raise PermissionDenied("Insufficient permissions")

            users = User.objects.all()
            serializer = RegisterUserSerializer(users, many=True)
            return self._success_response(
                data=serializer.data, message="Users retrieved successfully"
            )
        except PermissionDenied as e:
            return self._error_response(
                message=str(e), status_code=status.HTTP_403_FORBIDDEN
            )
        except (RuntimeError, ValueError, AttributeError, IntegrityError):
            return self._error_response(
                message="An error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Change user password",
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
        responses={
            200: "Password changed successfully",
            400: "Invalid input",
            403: "Permission denied",
            404: "User not found",
            500: "Internal Server Error",
        },
    )
    @action(detail=True, methods=["put"])
    def change_password(self, request, pk=None):
        """Change a user's password.

        Args:
            request: HTTP request object containing old_password and new_password
            pk: Primary key of the user whose password is being changed

        Returns:
            Response with success/error message and appropriate status code

        Raises:
            PermissionDenied: If user doesn't have permission
            ObjectDoesNotExist: If user not found
            ValidationError: If passwords invalid/missing
        """
        try:
            if not self._check_user_permission(request, pk):
                raise PermissionDenied("Insufficient permissions")

            user = User.objects.get(pk=pk)
            old_password = request.data.get("old_password")
            new_password = request.data.get("new_password")

            if not old_password or not new_password:
                raise ValidationError("Both old and new passwords are required")

            if not check_password(old_password, user.password):
                raise ValidationError("Invalid old password")

            user.password = make_password(new_password)
            user.save()
            return self._success_response(message="Password changed successfully")
        except ObjectDoesNotExist:
            return self._error_response(
                message="User not found", status_code=status.HTTP_404_NOT_FOUND
            )
        except PermissionDenied as e:
            return self._error_response(
                message=str(e), status_code=status.HTTP_403_FORBIDDEN
            )
        except ValidationError as e:
            return self._error_response(
                message=str(e), status_code=status.HTTP_400_BAD_REQUEST
            )
        except (RuntimeError, ValueError, AttributeError) as e:
            return self._error_response(
                message="An error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Create superuser (superuser only)",
        request_body=RegisterUserSerializer,
        responses={
            201: RegisterUserSerializer,
            403: "Permission denied",
            500: "Internal Server Error",
        },
    )
    @action(detail=False, methods=["post"])
    @permission_classes([IsSuperUser])
    def create_superuser(self, request):
        """Create a superuser - only accessible by existing superusers"""
        try:
            if not self._check_superuser_permission(request):
                raise PermissionDenied("Insufficient permissions")

            # Ensure is_superuser is set to True
            request.data["is_superuser"] = True
            request.data["is_active"] = True
            request.data["is_email_verified"] = True

            serializer = RegisterUserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return self._success_response(
                    data=serializer.data,
                    message="Superuser created successfully",
                    status_code=status.HTTP_201_CREATED,
                )
            return self._error_response(
                message="Superuser creation failed", errors=serializer.errors
            )
        except PermissionDenied as e:
            return self._error_response(
                message=str(e), status_code=status.HTTP_403_FORBIDDEN
            )
        except (ValidationError, IntegrityError, PermissionError):
            return self._error_response(
                message="An error occurred during superuser creation",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Create staff user (staff/superuser only)",
        request_body=RegisterUserSerializer,
        responses={
            201: RegisterUserSerializer,
            403: "Permission denied",
            500: "Internal Server Error",
        },
    )
    @action(detail=False, methods=["post"])
    @permission_classes([IsStaffOrSuperUser])
    def create_staff(self, request):
        """Create a staff user - accessible by superusers and staff"""
        try:
            if not self._check_staff_permission(request):
                raise PermissionDenied("Insufficient permissions")

            # Ensure is_staff is set to True
            request.data["is_staff"] = True
            request.data["is_active"] = True
            request.data["is_email_verified"] = True

            serializer = RegisterUserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return self._success_response(
                    data=serializer.data,
                    message="Staff user created successfully",
                    status_code=status.HTTP_201_CREATED,
                )
            return self._error_response(
                message="Staff user creation failed", errors=serializer.errors
            )
        except PermissionDenied as e:
            return self._error_response(
                message=str(e), status_code=status.HTTP_403_FORBIDDEN
            )
        except (RuntimeError, ValueError, AttributeError, ObjectDoesNotExist) as e:
            print(f"An error occurred during staff user creation: {str(e)}")
            return self._error_response(
                message=f"An unexpected error occurred: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def test_celery(self, _):
        """Test endpoint to verify Celery is working"""
        try:
            result = test_celery.delay()
            return self._success_response(
                message="Celery task queued successfully", data={"task_id": result.id}
            )
        except (ConnectionError, TimeoutError, RuntimeError) as e:
            return self._error_response(
                message=f"Error testing Celery: {str(e)}",
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
        """Resend verification email to an unverified user"""
        try:
            serializer = ResendVerificationEmailSerializer(data=request.data)
            if not serializer.is_valid():
                return self._error_response(
                    message="Invalid request data",
                    errors=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            email = serializer.validated_data["email"]

            try:
                user = User.objects.get(email=email)
            except ObjectDoesNotExist:
                return self._error_response(
                    message="User not found.", status_code=status.HTTP_404_NOT_FOUND
                )

            # Use the existing auth_key
            auth_key = user.auth_key

            if not auth_key:
                return self._error_response(
                    message="No verification key found for this user. Please register again or contact support.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            # Queue the email sending task with the existing auth_key
            app = __import__("backend.celery", fromlist=["app"]).app

            print(f"Queueing re-verification email for {email}")
            try:
                result = app.send_task(
                    "APIs.tasks.send_verification_email", args=[email, auth_key]
                )
                return self._success_response(
                    message="Verification email queued for resending.",
                    data={"task_id": result.id},
                    status_code=status.HTTP_200_OK,
                )
            except (ConnectionError, TimeoutError) as e:
                print(f"Celery task queuing failed for resend: {str(e)}")
                return self._error_response(
                    message=f"Failed to queue verification email resend task: {str(e)}",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except ValidationError as e:
            return self._error_response(
                message="Invalid data provided.",
                errors=e.detail,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except (RuntimeError, ValueError, AttributeError, ObjectDoesNotExist) as e:
            print(f"Unexpected error in resend_verification_email: {str(e)}")
            return self._error_response(
                message=f"An unexpected error occurred: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
