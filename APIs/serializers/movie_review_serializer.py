from rest_framework import serializers
from APIs.models.movie_comment_model import MovieComment
from APIs.models.user_model import User # Import User model for nested serialization

class MovieReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    movie_name = serializers.CharField(source='movie.name', read_only=True)

    class Meta:
        model = MovieComment
        fields = ['id', 'user', 'username', 'movie', 'movie_name', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['user', 'movie', 'created_at', 'updated_at']

    def create(self, validated_data):
        # The user and movie will be set in the view based on the request
        return MovieComment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.comment = validated_data.get('comment', instance.comment)
        instance.save()
        return instance
