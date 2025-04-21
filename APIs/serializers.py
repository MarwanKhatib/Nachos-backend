from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Genre, User


class RegisterUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    birth_date = serializers.DateField()  # Add birth_date to the serializer

    def create(self, validated_data):
        email = validated_data["email"]
        username = validated_data["username"]
        password = validated_data["password"]
        birth_date = validated_data["birth_date"]

        # Use the custom manager to register the user
        user = User.objects.register_user(
            email=email, username=username, password=password, birth_date=birth_date
        )
        return user


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

        if not user.verify_email(key):
            raise serializers.ValidationError({"key": "Invalid verification key."})

        return data


class SelectGenresSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    genre_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)

    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        return value

    def validate_genre_ids(self, value):
        valid_genres = Genre.objects.filter(id__in=value)
        if len(valid_genres) != len(value):
            raise serializers.ValidationError("One or more genre IDs are invalid.")
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Call the parent class's validate method to authenticate the user
        data = super().validate(attrs)

        # Check if the user has verified their email
        if not self.user.is_email_verified:
            raise ValidationError("Email is not verified.")

        return data


class UserGenresSerializer(serializers.Serializer):
    genres = serializers.ListField(child=serializers.CharField())


# a serializer for director - actor - writer - producer - genre - language
class PairStructuresSerializer (serializers.Serializer) :
    name = serializers.CharField()

class MovieSerializer ( serializers.Serializer ) :
    name = serializers.CharField()
    description = serializers.CharField()
    trailer = serializers.CharField()
    poster = serializers.CharField()
    language = serializers.IntegerField()


class MovieInfosSerializer ( serializers.Serializer ) :
    name = serializers.CharField()
    description = serializers.CharField()
    trailer = serializers.CharField()
    poster = serializers.CharField()
    language = serializers.CharField()

    actors = serializers.ListField(child=serializers.CharField())
    writers = serializers.ListField(child=serializers.CharField())
    producers = serializers.ListField(child=serializers.CharField())
    directors = serializers.ListField(child=serializers.CharField())
    genres = serializers.ListField(child=serializers.CharField())

class WatchlistItemSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    movie_id = serializers.IntegerField()    

class RateMovieSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    movie_id = serializers.IntegerField()
    rate = serializers.FloatField(min_value=0, max_value=5)