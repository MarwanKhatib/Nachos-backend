"""
This module contains serializers for movie-related data models.
It provides serialization/deserialization for movie information, watchlists,
ratings, comments and other movie-related structures.
"""

from rest_framework import serializers

from APIs.models import MovieCommunity


class PairStructuresSerializer(serializers.Serializer):
    """
    Serializer for handling pair structure data.
    Provides serialization and deserialization of name-based pair structures.
    """

    name = serializers.CharField()

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        return instance


class MovieSerializer(serializers.Serializer):
    """
    Serializer for movie data.
    Handles serialization and deserialization of basic movie information.
    """

    id = serializers.IntegerField(read_only=True) # Add movie ID
    name = serializers.CharField()
    description = serializers.CharField()
    trailer = serializers.CharField()
    poster = serializers.CharField()
    language = serializers.CharField(source='language.name', allow_null=True, required=False)

    def create(self, validated_data):
        """Create and return a new movie instance"""
        return validated_data

    def update(self, instance, validated_data):
        """Update and return an existing movie instance"""
        fields = ["name", "description", "trailer", "poster", "language"]

        for field in fields:
            setattr(
                instance, field, validated_data.get(field, getattr(instance, field))
            )

        return instance


class MovieInfosSerializer(serializers.Serializer):
    """
    Serializer for detailed movie information including cast and crew details.
    Handles serialization of extended movie data including related personnel and genres.
    """

    name = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True)
    trailer = serializers.URLField(allow_blank=True)
    poster = serializers.URLField(allow_blank=True)
    language = serializers.CharField(max_length=50)
    actors = serializers.ListField(
        child=serializers.CharField(max_length=100), allow_empty=True
    )
    writers = serializers.ListField(
        child=serializers.CharField(max_length=100), allow_empty=True
    )
    producers = serializers.ListField(
        child=serializers.CharField(max_length=100), allow_empty=True
    )
    directors = serializers.ListField(
        child=serializers.CharField(max_length=100), allow_empty=True
    )
    genres = serializers.ListField(
        child=serializers.CharField(max_length=50), allow_empty=True
    )

    def validate_url_field(self, value, field_name):
        """Generic URL field validator"""
        if value and not value.startswith(("http://", "https://")):
            raise serializers.ValidationError(f"Invalid URL format for {field_name}")
        return value

    def validate_trailer(self, value):
        """Validate trailer URL format"""
        return self.validate_url_field(value, "trailer")

    def validate_poster(self, value):
        """Validate poster URL format"""
        return self.validate_url_field(value, "poster")

    def create(self, validated_data):
        """Create and return a new movie info instance"""
        return validated_data

    def update(self, instance, validated_data):
        """Update and return an existing movie info instance"""
        fields = [
            "name",
            "description",
            "trailer",
            "poster",
            "language",
            "actors",
            "writers",
            "producers",
            "directors",
            "genres",
        ]

        for field in fields:
            setattr(
                instance, field, validated_data.get(field, getattr(instance, field))
            )

        return instance


class WatchlistItemSerializer(serializers.Serializer):
    """
    Serializer for watchlist items.
    Handles serialization and validation of user's watchlist entries.
    """

    movie_id = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        """Validate watchlist item data"""
        if attrs["movie_id"] <= 0:
            raise serializers.ValidationError("Movie ID must be a positive integer")
        return attrs

    def create(self, validated_data):
        """Create and return a new watchlist item"""
        return validated_data

    def update(self, instance, validated_data):
        """Update and return an existing watchlist item"""
        instance.movie_id = validated_data.get("movie_id", instance.movie_id)
        return instance


class RateMovieSerializer(serializers.Serializer):
    """
    Serializer for movie ratings.
    Handles serialization and validation of user movie ratings.
    """

    movie_id = serializers.IntegerField(min_value=1)
    rate = serializers.FloatField(min_value=0, max_value=5)

    def validate(self, attrs):
        """Validate rating data"""
        if attrs["movie_id"] <= 0:
            raise serializers.ValidationError("Movie ID must be a positive integer")

        if attrs["rate"] < 0 or attrs["rate"] > 5:
            raise serializers.ValidationError("Rate must be between 0 and 5")

        return attrs

    def create(self, validated_data):
        """Create and return a new rating"""
        return validated_data

    def update(self, instance, validated_data):
        """Update and return an existing rating"""
        instance.rate = validated_data.get("rate", instance.rate)
        return instance


class MovieCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for movie comments.
    Handles serialization of user comments on movies.
    """

    username = serializers.CharField(source="user.username", read_only=True)
    content = serializers.CharField(required=True, min_length=1)
    add_date = serializers.DateTimeField(read_only=True)

    class Meta:
        """
        Metadata class for MovieCommentSerializer.
        Specifies the model and fields to be serialized.
        """

        model = MovieCommunity
        fields = ["id", "username", "content", "add_date"]

    def validate_content(self, value):
        """Validate comment content"""
        if not value.strip():
            raise serializers.ValidationError("Comment content cannot be empty")
        return value.strip()


class AddToWatchlistSerializer(serializers.Serializer):
    """
    Serializer for adding a movie to a user's watchlist.
    """

    movie_id = serializers.IntegerField(min_value=1)
