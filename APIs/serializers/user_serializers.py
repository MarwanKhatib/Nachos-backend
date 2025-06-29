from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenBlacklistSerializer as BlacklistRefreshTokenSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken # Import RefreshToken for type hinting
import logging
from typing import cast, Type # Import Type for type hinting
from django.db import models # Import models
from django.db.models import QuerySet, Manager # Import Manager
from django.db.models.manager import BaseManager # Keep BaseManager for CustomUserManager inheritance

from APIs.models import Genre, User
from APIs.managers import CustomUserManager # Import CustomUserManager
from django.contrib.auth.hashers import check_password
from django.db.models import Manager # Import Manager for type hinting
from APIs.serializers.movie_serializers import MovieWatchlistSerializer # Import MovieWatchlistSerializer


class RegisterUserSerializer(serializers.Serializer):
    """
    Serializer for user registration. Only allows email, username, password, and birth_date.
    """
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=cast(CustomUserManager, User.objects).all(),
                message="A user with this email already exists.",
            )
        ],
        required=True,
    )
    username = serializers.CharField(
        validators=[
            UniqueValidator(
                queryset=cast(CustomUserManager, User.objects).all(),
                message="A user with this username already exists.",
            )
        ],
        required=True,
    )
    password = serializers.CharField(write_only=True, required=True)
    birth_date = serializers.DateField(required=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True) # Added profile_picture field

    def validate(self, attrs):
        # Ensure self.initial_data is a dictionary before calling .keys()
        if not isinstance(self.initial_data, dict):
            raise ValidationError({"non_field_errors": ["Invalid request data format."]})

        allowed_fields = {"email", "username", "password", "birth_date", "profile_picture"}
        extra_fields = set(self.initial_data.keys()) - allowed_fields
        if extra_fields:
            raise ValidationError({
                "non_field_errors": [
                    f"Unexpected field(s): {', '.join(extra_fields)}. Only email, username, password, birth_date, and profile_picture are allowed."
                ]
            })
        return attrs

    def create(self, validated_data):
        email = validated_data["email"]
        username = validated_data["username"]
        password = validated_data["password"]
        birth_date = validated_data["birth_date"]
        profile_picture = validated_data.get("profile_picture") # Get profile_picture

        user = cast(CustomUserManager, User.objects).register_user(
            email=email,
            username=username,
            password=password,
            birth_date=birth_date,
            profile_picture=profile_picture # Pass profile_picture
        )
        return user

    def update(self, instance, validated_data):
        # Update the user instance with validated data
        for attr, value in validated_data.items():
            if attr == "password":
                instance.set_password(value)
            elif attr == "profile_picture": # Handle profile_picture update
                instance.profile_picture = value
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance


class UserAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for admin user management.
    Includes all fields for detailed user information and management.
    """
    watchlist = MovieWatchlistSerializer(many=True, read_only=True) # Nested serializer for watchlist
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'birth_date',
            'watched_no', 'join_date', 'profile_picture', 'is_email_verified',
            'is_staff', 'is_superuser', 'is_active', 'watchlist', 'password'
        ]
        read_only_fields = ['id', 'join_date', 'watched_no', 'is_email_verified', 'is_staff', 'is_superuser', 'is_active']
        extra_kwargs = {'password': {'write_only': True, 'required': False}} # Ensure password is write-only and not always required

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        
        # Extract flags from context, which are set by the API views
        is_superuser_creation = self.context.get('is_superuser_creation', False)
        is_staff_creation = self.context.get('is_staff_creation', False)
        is_active_context = self.context.get('is_active', False)
        is_email_verified_context = self.context.get('is_email_verified', False)

        # Initialize user flags based on context or default to False
        is_superuser = is_superuser_creation
        is_staff = is_staff_creation or is_superuser_creation # Superusers are also staff
        is_active = is_active_context
        is_email_verified = is_email_verified_context
        
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            birth_date=validated_data['birth_date'],
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            profile_picture=validated_data.get('profile_picture'),
            is_superuser=is_superuser,
            is_staff=is_staff,
            is_active=is_active,
            is_email_verified=is_email_verified
        )

        if password:
            user.set_password(password)

        user.save()
        return user

    def update(self, instance, validated_data):
        # Handle password update separately
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile management (retrieve and update).
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'birth_date', 'profile_picture', 'is_email_verified']
        read_only_fields = ['email', 'username', 'is_email_verified'] # Email and username should not be changed via profile update

    profile_picture = serializers.ImageField(required=False, allow_null=True)

    def update(self, instance, validated_data):
        # Handle profile picture update separately if it's a file
        if 'profile_picture' in validated_data:
            instance.profile_picture = validated_data.pop('profile_picture')

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class VerifyEmailSerializer(serializers.Serializer):
    """
    Serializer for verifying a user's email with a verification code.
    """
    email = serializers.EmailField()
    key = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        key = attrs.get("key")
        try:
            user = cast(CustomUserManager, User.objects).get(email=email)
        except User.DoesNotExist:
            logging.error(f"Verification failed: User with email {email} does not exist.")
            raise serializers.ValidationError({"email": "User with this email does not exist."})
        if user.is_email_verified:
            logging.error(f"Verification failed: Email {email} already verified.")
            raise serializers.ValidationError({"email": "Email is already verified."})
        if not user.auth_key:
            logging.error(f"Verification failed: No auth_key for user {email}.")
            raise serializers.ValidationError({"key": "No verification key found. Please request a new verification email."})
        if key.strip() != user.auth_key:
            logging.error(f"Verification failed: Invalid key for user {email}.")
            raise serializers.ValidationError({"key": "Verification key is invalid."})
        attrs["user"] = user
        logging.info(f"Verification passed for user {email}.")
        return attrs
    
class SelectGenresSerializer(serializers.Serializer):
    """
    Serializer for selecting genres by their IDs for a user.
    """
    genre_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)

    def validate_genre_ids(self, value):
        valid_genres = cast(Manager, Genre.objects).filter(id__in=value)
        if len(valid_genres) != len(value):
            raise serializers.ValidationError("One or more genre IDs are invalid.")
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that checks if the user's email is verified before issuing tokens.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user or not self.user.is_email_verified: # Added check for self.user
            raise ValidationError("Email is not verified.")
        return data


class UserGenresSerializer(serializers.Serializer):
    """
    Serializer for listing a user's genres as strings.
    """
    genres = serializers.ListField(child=serializers.CharField())


class ResendVerificationEmailSerializer(serializers.Serializer):
    """
    Serializer for requesting a resend of the verification email.
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = cast(CustomUserManager, User.objects).get(email=value)
            if user.is_email_verified:
                raise serializers.ValidationError("Email is already verified.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")


class RequestPasswordResetSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            cast(CustomUserManager, User.objects).get(email=value)
        except User.DoesNotExist:
            # We don't want to expose whether an email exists for security reasons
            # So, we return a success message even if the user doesn't exist.
            # The actual email sending logic will handle the non-existent user.
            pass
        return value


class SetNewPasswordSerializer(serializers.Serializer):
    """
    Serializer for setting a new password after a reset request.
    """
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError({"new_password": "New passwords must match."})

        try:
            user = cast(CustomUserManager, User.objects).get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User with this email does not exist."})

        # The code verification is now handled by a separate API, so we don't check it here.
        # We assume that if this endpoint is called, the code has already been verified.

        attrs['user'] = user
        return attrs


class VerifyPasswordResetCodeSerializer(serializers.Serializer):
    """
    Serializer for verifying a password reset code.
    """
    email = serializers.EmailField(required=True)
    code = serializers.CharField(max_length=6, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        code = attrs.get('code')

        try:
            user = cast(CustomUserManager, User.objects).get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User with this email does not exist."})

        if user.password_reset_code != code:
            raise serializers.ValidationError({"code": "Invalid password reset code."})

        attrs['user'] = user
        return attrs


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer for login using email and password, with email verification check.
    """
    username_field = "email"
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        try:
            email = attrs.get("email")
            password = attrs.get("password")
            if not email or not password:
                raise ValidationError("Email and password are required.")
            try:
                user = cast(CustomUserManager, User.objects).get(email=email)
            except User.DoesNotExist:
                logging.error(f"No user found with email: {email}")
                raise ValidationError("No user found with this email.")
            if user.check_password(password):
                if not user.is_email_verified:
                    logging.error(f"Login attempt with unverified email: {email}")
                    raise ValidationError("Email is not verified.")
                refresh = cast(RefreshToken, self.get_token(user)) # Explicitly cast to RefreshToken
                data = {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
                data["user_id"] = user.id
                data["username"] = user.username
                data["email"] = user.email
                return data
            else:
                logging.error(f"Incorrect password for email: {email}")
                raise ValidationError("Incorrect password.")
        except Exception as e:
            logging.error(f"Error in EmailTokenObtainPairSerializer validation: {e}")
            raise e
