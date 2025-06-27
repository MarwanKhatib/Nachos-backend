import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.apps import apps
from django.db.models import signals

# Manually import models to ensure they are loaded
Movie = apps.get_model('APIs', 'Movie')
MovieCommunity = apps.get_model('APIs', 'MovieCommunity')
User = apps.get_model('APIs', 'User')
UserWatchedMovie = apps.get_model('APIs', 'UserWatchedMovie')

from APIs.serializers.movie_serializers import MovieCommentSerializer

logger = logging.getLogger(__name__)


class AddCommunityComment(APIView):
    def post(self, request):
        user_id_req = request.data.get("user_id")
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for adding community comment.")
        
        # Step 1: Validate input data
        movie_id = request.data.get("movie_id")
        content = request.data.get("content")

        # Step 2: Check if the user and movie exist
        try:
            user = User.objects.get(id=user_id_req)
            movie = Movie.objects.get(id=movie_id)
        except User.DoesNotExist:
            logger.warning(f"Add community comment failed for user {user_id_req} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Movie.DoesNotExist:
            logger.warning(f"Add community comment failed for user {user_id_req} to {path}: Movie not found.")
            return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

        # Step 3: Check if the user has watched the movie
        if not UserWatchedMovie.objects.filter(user=user, movie=movie).exists():
            logger.warning(f"Add community comment failed for user {user_id_req} to {path}: User has not watched the movie.")
            return Response(
                {"error": "You must watch the movie before commenting."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Step 4: Create the comment
        try:
            comment = MovieCommunity.objects.create(movie=movie, user=user, content=content)
            logger.info(f"Community comment added successfully by user {user_id_req} to {path} for movie {movie_id}.")
            return Response(
                {"message": "Comment added successfully.", "comment_id": comment.id},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Add community comment failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteCommunityComment(APIView):
    def delete(self, request, comment_id):
        user_id_req = request.query_params.get("user_id")
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for deleting community comment {comment_id}.")
        
        # Step 1: Get the user ID from the request
        # Step 2: Check if the user exists
        try:
            user = User.objects.get(id=user_id_req)
        except User.DoesNotExist:
            logger.warning(f"Delete community comment failed for user {user_id_req} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Step 3: Retrieve the comment
        try:
            comment = MovieCommunity.objects.get(id=comment_id)
        except MovieCommunity.DoesNotExist:
            logger.warning(f"Delete community comment failed for user {user_id_req} to {path}: Comment {comment_id} not found.")
            return Response(
                {"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Step 4: Ensure the user is the owner of the comment
        if comment.user != user:
            logger.warning(f"Delete community comment failed for user {user_id_req} to {path}: Unauthorized to delete comment {comment_id}.")
            return Response(
                {"error": "You are not authorized to delete this comment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Step 5: Delete the comment
        try:
            comment.delete()
            logger.info(f"Community comment {comment_id} deleted successfully by user {user_id_req} to {path}.")
            return Response(
                {"message": "Comment deleted successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Delete community comment failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetMovieComments(APIView):
    def get(self, request, movie_id):
        user_id_req = request.query_params.get("user_id")
        path = request.path
        logger.info(f"Request by user {user_id_req} to {path} for getting movie comments for movie {movie_id}.")
        
        # Step 1: Extract user_id from the request
        # Step 2: Validate user_id
        if not user_id_req:
            logger.warning(f"Get movie comments failed for path {path}: user_id is required.")
            return Response(
                {"error": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id_req)
        except User.DoesNotExist:
            logger.warning(f"Get movie comments failed for user {user_id_req} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Step 3: Check if the movie exists
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            logger.warning(f"Get movie comments failed for user {user_id_req} to {path}: Movie {movie_id} not found.")
            return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

        # Step 4: Verify that the user has watched the movie
        if not UserWatchedMovie.objects.filter(user=user, movie=movie).exists():
            logger.warning(f"Get movie comments failed for user {user_id_req} to {path}: User has not watched the movie.")
            return Response(
                {"error": "You must watch the movie to view its comments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Step 5: Retrieve all comments for the movie
        try:
            comments = MovieCommunity.objects.filter(movie=movie).order_by("-add_date")

            # Step 6: Serialize the data
            serializer = MovieCommentSerializer(comments, many=True)
            logger.info(f"Movie comments retrieved successfully by user {user_id_req} to {path} for movie {movie_id}.")
            # Step 7: Return the serialized data
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Get movie comments failed for user {user_id_req} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetWatchedMovieIds(APIView):
    def get(self, request, user_id):
        path = request.path
        logger.info(f"Request by user {user_id} to {path} for getting watched movie IDs.")
        
        # Step 1: Check if the user exists
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.warning(f"Get watched movie IDs failed for user {user_id} to {path}: User not found.")
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Step 2: Retrieve all watched movie IDs for the user
        try:
            watched_movies = UserWatchedMovie.objects.filter(user=user).values_list(
                "movie_id", flat=True
            )
            logger.info(f"Watched movie IDs retrieved successfully by user {user_id} to {path}.")
            # Step 3: Convert the QuerySet to a list and return it
            return Response(
                {"watched_movie_ids": list(watched_movies)}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Get watched movie IDs failed for user {user_id} to {path}: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
