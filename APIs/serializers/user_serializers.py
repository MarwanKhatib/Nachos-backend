from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
import logging

from APIs.models import Genre, User


class RegisterUserSerializer(serializers.Serializer):
    """
    Serializer for user registration. Only allows email, username, password, and birth_date.
    """
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="A user with this email already exists.",
            )
        ],
        required=True,
    )
    username = serializers.CharField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="A user with this username already exists.",
            )
        ],
        required=True,
    )
    password = serializers.CharField(write_only=True, required=True)
    birth_date = serializers.DateField(required=True)

    def validate(self, attrs):
        allowed_fields = {"email", "username", "password", "birth_date"}
        extra_fields = set(self.initial_data.keys()) - allowed_fields
        if extra_fields:
            raise ValidationError({
                "non_field_errors": [
                    f"Unexpected field(s): {', '.join(extra_fields)}. Only email, username, password, and birth_date are allowed."
                ]
            })
        return attrs

    def create(self, validated_data):
        email = validated_data["email"]
        username = validated_data["username"]
        password = validated_data["password"]
        birth_date = validated_data["birth_date"]

        user = User.objects.register_user(
            email=email,
            username=username,
            password=password,
            birth_date=birth_date,
        )
        return user

    def update(self, instance, validated_data):
        # Update the user instance with validated data
        for attr, value in validated_data.items():
            if attr == "password":
                instance.set_password(value)
            else:
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
            user = User.objects.get(email=email)
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
        valid_genres = Genre.objects.filter(id__in=value)
        if len(valid_genres) != len(value):
            raise serializers.ValidationError("One or more genre IDs are invalid.")
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that checks if the user's email is verified before issuing tokens.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_email_verified:
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
            user = User.objects.get(email=value)
            if user.is_email_verified:
                raise serializers.ValidationError("Email is already verified.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")


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
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                logging.error(f"No user found with email: {email}")
                raise ValidationError("No user found with this email.")
            if user.check_password(password):
                if not user.is_email_verified:
                    logging.error(f"Login attempt with unverified email: {email}")
                    raise ValidationError("Email is not verified.")
                refresh = self.get_token(user)
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
