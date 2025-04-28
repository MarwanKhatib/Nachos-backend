from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import *


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


class MovieCommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = MovieCommunity
        fields = ["id", "username", "content", "add_date"]


class CreateGroupSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    group_name = serializers.CharField(max_length=50)
    description = serializers.CharField()
    
    def validate_group_name(self, value):
        if Group.objects.filter(name=value).exists():
            raise serializers.ValidationError("Group name must be unique.")
        return value
    

class JoinGroupSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    group_id = serializers.IntegerField()

    def validate(self, data):
        user_id = data.get("user_id")
        group_id = data.get("group_id")

        # Check if user exists
        if not User.objects.filter(id=user_id).exists():
            raise serializers.ValidationError({"user_id": "User does not exist."})

        # Check if group exists
        if not Group.objects.filter(id=group_id).exists():
            raise serializers.ValidationError({"group_id": "Group does not exist."})

        # Check if user is already in the group
        if UserGroup.objects.filter(user_id=user_id, group_id=group_id).exists():
            raise serializers.ValidationError({"error": "User is already in the group."})

        return data
    
class BlockUserSerializer(serializers.Serializer):
    admin_user_id = serializers.IntegerField()
    group_id = serializers.IntegerField()
    blocked_user_id = serializers.IntegerField()

    def validate(self, data):
        admin_user_id = data.get("admin_user_id")
        group_id = data.get("group_id")
        blocked_user_id = data.get("blocked_user_id")

        # Check if the admin user exists and is an admin in the group
        admin_group = UserGroup.objects.filter(user_id=admin_user_id, group_id=group_id, is_admin=True).first()
        if not admin_group:
            raise serializers.ValidationError({"admin_user_id": "User is not an admin of the group."})

        # Check if the blocked user exists in the group
        if not UserGroup.objects.filter(user_id=blocked_user_id, group_id=group_id).exists():
            raise serializers.ValidationError({"blocked_user_id": "User is not in the group."})

        return data
    
class UnblockUserSerializer(serializers.Serializer):
    admin_user_id = serializers.IntegerField()
    group_id = serializers.IntegerField()
    unblocked_user_id = serializers.IntegerField()

    def validate(self, data):
        admin_user_id = data.get("admin_user_id")
        group_id = data.get("group_id")
        unblocked_user_id = data.get("unblocked_user_id")

        # Check if the admin user exists and is an admin in the group
        admin_group = UserGroup.objects.filter(user_id=admin_user_id, group_id=group_id, is_admin=True).first()
        if not admin_group:
            raise serializers.ValidationError({"admin_user_id": "User is not an admin of the group."})

        # Check if the unblocked user exists in the group and is blocked
        user_group = UserGroup.objects.filter(user_id=unblocked_user_id, group_id=group_id, is_blocked=True).first()
        if not user_group:
            raise serializers.ValidationError({"unblocked_user_id": "User is not blocked in this group."})

        return data

class WritePostSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    group_id = serializers.IntegerField()
    content = serializers.CharField(max_length=255)

    def validate(self, data):
        user_id = data.get("user_id")
        group_id = data.get("group_id")

        # Check if the user exists
        if not User.objects.filter(id=user_id).exists():
            raise serializers.ValidationError({"user_id": "User does not exist."})

        # Check if the group exists
        if not Group.objects.filter(id=group_id).exists():
            raise serializers.ValidationError({"group_id": "Group does not exist."})

        # Check if the user is a member of the group
        if not UserGroup.objects.filter(user_id=user_id, group_id=group_id, is_blocked=False).exists():
            raise serializers.ValidationError({"error": "You are not a member of this group or you are blocked."})

        return 

class CommentPostSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    post_id = serializers.IntegerField()
    content = serializers.CharField(max_length=255)

class EditCommentSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    comment_id = serializers.IntegerField()
    content = serializers.CharField(max_length=255)