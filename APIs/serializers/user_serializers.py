from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)

from APIs.models import Genre, User


class RegisterUserSerializer(serializers.Serializer):
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="A user with this email already exists.",
            )
        ],
        required=False,
    )
    username = serializers.CharField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="A user with this username already exists.",
            )
        ],
        required=False,
    )
    password = serializers.CharField(write_only=True, required=False)
    birth_date = serializers.DateField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    is_active = serializers.BooleanField(required=False, default=False)
    is_email_verified = serializers.BooleanField(required=False, default=False)

    def create(self, validated_data):
        email = validated_data["email"]
        username = validated_data["username"]
        password = validated_data["password"]
        birth_date = validated_data["birth_date"]
        first_name = validated_data["first_name"]
        last_name = validated_data["last_name"]

        user = User.objects.register_user(
            email=email,
            username=username,
            password=password,
            birth_date=birth_date,
            first_name=first_name,
            last_name=last_name,
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
    email = serializers.EmailField()
    key = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get("email")
        key = data.get("key")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "User with this email does not exist."}
            )

        if user.is_email_verified:
            raise serializers.ValidationError({"email": "Email is already verified."})

        if not user.auth_key:
            raise serializers.ValidationError(
                {
                    "key": "No verification key found. Please request a new verification email."
                }
            )

        # Store the user in the validated data for use in the view
        data["user"] = user
        return data


class SelectGenresSerializer(serializers.Serializer):
    genre_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)

    def validate_genre_ids(self, value):
        valid_genres = Genre.objects.filter(id__in=value)
        if len(valid_genres) != len(value):
            raise serializers.ValidationError("One or more genre IDs are invalid.")
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_email_verified:
            raise ValidationError("Email is not verified.")
        return data


class UserGenresSerializer(serializers.Serializer):
    genres = serializers.ListField(child=serializers.CharField())


class ResendVerificationEmailSerializer(serializers.Serializer):
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
    username_field = "email"
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        try:
            email = attrs.get("email")
            password = attrs.get("password")

            if not email or not password:
                raise ValidationError("Email and password are required.")

            # Try to authenticate using email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise ValidationError("No user found with this email.")

            # Authenticate the user with the password
            if user.check_password(password):
                # Also check if the email is verified before allowing login
                if not user.is_email_verified:
                    raise ValidationError("Email is not verified.")

                # If authentication is successful, get the tokens
                refresh = self.get_token(user)
                data = {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }

                # Include user details in the response
                data["user_id"] = user.id
                data["username"] = user.username
                data["email"] = user.email

                return data
            else:
                raise ValidationError("Incorrect password.")
        except Exception as e:
            # Log the exception for debugging
            print(f"Error in EmailTokenObtainPairSerializer validation: {e}")
            # Re-raise the exception so Django logs the full traceback
            raise e
