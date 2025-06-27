import logging
import threading
from typing import cast # Import cast

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
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken # New import

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from APIs.models.user_model import User
from APIs.serializers.user_serializers import (
    EmailTokenObtainPairSerializer,
    RegisterUserSerializer,
    ResendVerificationEmailSerializer,
    VerifyEmailSerializer,
    RequestPasswordResetSerializer,
    SetNewPasswordSerializer,
)
from APIs.tasks import create_user_suggestions, send_verification_email, send_password_reset_email

# Removed direct import of TokenBlacklistSerializer as it's being bypassed
# from rest_framework_simplejwt.serializers import (
#     TokenBlacklistSerializer as BlacklistRefreshTokenSerializer,
# )


class AuthenticationViewSet(ViewSet):
    """ViewSet for handling authentication-related operations."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

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
        operation_description="Request password reset email",
        request_body=RequestPasswordResetSerializer,
        responses={
            200: "Password reset email sent successfully (if user exists)",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    @action(detail=False, methods=["post"])
    def request_password_reset(self, request):
        """
        Requests a password reset email to be sent to the user.
        """
        serializer = RequestPasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return self._error_response(
                message="Invalid request data.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        email = cast(dict, serializer.validated_data)["email"]
        try:
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)

            # Send email asynchronously
            threading.Thread(target=send_password_reset_email, args=[email, uidb64, token]).start()

            return self._success_response(
                message="Password reset email sent successfully. Please check your inbox.",
                status_code=status.HTTP_200_OK,
            )
        except ObjectDoesNotExist:
            # For security reasons, always return a success message even if the user doesn't exist.
            # This prevents enumeration of existing user accounts.
            logging.warning(f"Password reset requested for non-existent email: {email}")
            return self._success_response(
                message="If an account with that email exists, a password reset email has been sent.",
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            logging.error(f"Error requesting password reset for {email}: {str(e)}", exc_info=True)
            return self._error_response(
                message="An error occurred during password reset request.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Set new password using UID and token from reset email",
        request_body=SetNewPasswordSerializer,
        responses={
            200: "Password set successfully",
            400: "Invalid token or UID",
            404: "User not found",
            500: "Internal Server Error",
        },
    )
    @action(detail=False, methods=["post"])
    def set_new_password(self, request):
        """
        Sets a new password for the user using a UID and token from a reset email.
        """
        serializer = SetNewPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return self._error_response(
                message="Invalid request data.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = cast(dict, serializer.validated_data)
        uidb64 = validated_data["uidb64"]
        token = validated_data["token"]
        new_password = validated_data["new_password"]

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, ObjectDoesNotExist):
            user = None

        if user is not None and PasswordResetTokenGenerator().check_token(user, token):
            user.set_password(new_password)
            user.save()
            return self._success_response(
                message="Password set successfully.",
                status_code=status.HTTP_200_OK,
            )
        else:
            return self._error_response(
                message="The reset link is invalid or has expired.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    @swagger_auto_schema(
        operation_description="Logout user by blacklisting the refresh token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={"refresh": openapi.Schema(type=openapi.TYPE_STRING)},
        ),
        responses={
            200: "Logout successful",
            400: "Bad Request / Invalid token",
            500: "Internal Server Error",
        },
    )
    @action(detail=False, methods=["post"])
    def logout(self, request):
        """
        Logs out the user by blacklisting the provided refresh token.
        """
        try:
            refresh_token_string = request.data.get("refresh")
            if not refresh_token_string:
                raise ValidationError("Refresh token is required.")

            # Attempt to get the OutstandingToken and blacklist it directly
            try:
                token = RefreshToken(refresh_token_string)
                outstanding_token = OutstandingToken.objects.get(token=token.token) # Use token.token to get the JTI
                BlacklistedToken.objects.get_or_create(token=outstanding_token)
            except OutstandingToken.DoesNotExist:
                raise TokenError("Token not found or already blacklisted.")
            except TokenError:
                raise TokenError("Invalid refresh token.")

            return self._success_response(message="Logout successful.")
        except TokenError as e:
            return self._error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except ValidationError as e:
            return self._error_response(
                message="Logout failed.", errors=e.detail,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logging.error(f"Error during logout: {str(e)}", exc_info=True)
            return self._error_response(
                message="An error occurred during logout.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
