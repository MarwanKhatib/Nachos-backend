from rest_framework import serializers
from APIs.models import Movie, MovieCommunity

class PairStructuresSerializer(serializers.Serializer):
    name = serializers.CharField()

class MovieSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    trailer = serializers.CharField()
    poster = serializers.CharField()
    language = serializers.IntegerField()

class MovieInfosSerializer(serializers.Serializer):
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