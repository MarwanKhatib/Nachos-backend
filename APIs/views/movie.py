"""
Views for movie-related API endpoints.

This module contains view functions for handling movie-related API requests,
including retrieving movie details, managing watchlists, ratings and comments.
"""

import logging


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend


logger = logging.getLogger(__name__)

from APIs.models.actor_model import Actor
from APIs.models.director_model import Director
from APIs.models.genre_model import Genre
from APIs.models.movie_model import Movie
from APIs.models.movie_actor_model import MovieActor
from APIs.models.movie_comment_model import MovieComment
from APIs.models.movie_director_model import MovieDirector
from APIs.models.movie_genre_model import MovieGenre
from APIs.models.movie_producer_model import MovieProducer
from APIs.models.movie_writer_model import MovieWriter
from APIs.models.producer_model import Producer
from APIs.models.user_model import User
from APIs.models.community_model import UserGenre, UserSuggestionList, UserWatchedMovie
from APIs.models.writer_model import Writer
from typing import cast
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from APIs.serializers.movie_serializers import (
    MovieInfosSerializer,
    MovieSerializer,
    PairStructuresSerializer,
    RateMovieSerializer,
)
from APIs.serializers.movie_review_serializer import MovieReviewSerializer
from APIs.utils.suggestion_helpers import update_suggestions_by_rate


@swagger_auto_schema(
    method="get",
    operation_description="Get detailed information about a specific movie",
    operation_summary="Get movie details",
    responses={
        200: MovieInfosSerializer,
        404: openapi.Response(
            "Movie not found",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(
                        type=openapi.TYPE_STRING, description="Error message"
                    )
                },
            ),
        ),
    },
    tags=["Movies"],
)
@api_view(["GET"])
def get_movie(request, movie_id):
    logger.info(f"Attempting to retrieve movie with ID: {movie_id}")
    try:
        movie = Movie.objects.get(id=movie_id)
        logger.info(f"Successfully retrieved movie: {movie.name}")
    except Movie.DoesNotExist:
        logger.warning(f"Movie with ID {movie_id} not found.")
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error retrieving movie {movie_id}: {e}")
        return Response(
            {"error": "Internal server error."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    actors = Actor.objects.filter(
        id__in=MovieActor.objects.filter(movie_id=movie.id).values_list(
            "actor_id", flat=True
        )
    )
    writers = Writer.objects.filter(
        id__in=MovieWriter.objects.filter(movie_id=movie.id).values_list(
            "writer_id", flat=True
        )
    )
    producers = Producer.objects.filter(
        id__in=MovieProducer.objects.filter(movie_id=movie.id).values_list(
            "producer_id", flat=True
        )
    )
    directors = Director.objects.filter(
        id__in=MovieDirector.objects.filter(movie_id=movie.id).values_list(
            "director_id", flat=True
        )
    )
    genres = Genre.objects.filter(
        id__in=MovieGenre.objects.filter(movie_id=movie.id).values_list(
            "genre_id", flat=True
        )
    )

    movie_data = {
        "name": movie.name,
        "description": movie.description,
        "trailer": movie.trailer,
        "poster": movie.poster,
        "language": movie.language.name,
        "actors": [actor.name for actor in actors],
        "writers": [writer.name for writer in writers],
        "producers": [producer.name for producer in producers],
        "directors": [director.name for director in directors],
        "genres": [genre.name for genre in genres],
    }

    serializer = MovieInfosSerializer(data=movie_data)
    if serializer.is_valid():
        logger.info(f"Successfully serialized movie data for movie ID: {movie_id}")
        return Response(serializer.data)
    logger.error(f"Serializer errors for movie ID {movie_id}: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="post",
    operation_description="Rate a movie and update suggestions. The movie ID and rating are provided in the request body.",
    operation_summary="Rate a movie",
    security=[{"Bearer": []}],
    request_body=RateMovieSerializer, # Use the serializer directly for the request body
    responses={
        200: openapi.Response(
            "Success",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Movie rated successfully and suggestions updated.",
                    )
                },
            ),
        ),
        201: openapi.Response(
            "Created",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Movie rated successfully and suggestions updated.",
                    )
                },
            ),
        ),
        400: openapi.Response(
            "Bad Request",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_OBJECT)},
            ),
        ),
        404: openapi.Response(
            "Not Found",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"error": openapi.Schema(type=openapi.TYPE_STRING)},
            ),
        ),
    },
    tags=["Movies"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rate_movie(request): # Removed movie_id from function parameters
    logger.info(f"User {request.user.id} attempting to rate movie.")
    serializer = RateMovieSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(f"Invalid data for rate_movie: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    movie_id = cast(dict, serializer.validated_data)["movie_id"] # Get movie_id from validated data
    new_rating = cast(dict, serializer.validated_data)["rate"]

    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        logger.warning(f"Movie with ID {movie_id} not found for rating.")
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error checking movie existence for rating: {e}")
        return Response(
            {"error": "Internal server error."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        watched_movie, created = UserWatchedMovie.objects.get_or_create(
            user=user,
            movie=movie,
            defaults={"rate": new_rating},
        )

        old_rating = None
        if not created:
            old_rating = watched_movie.rate
            watched_movie.rate = new_rating
            watched_movie.save()
            logger.info(f"Updated rating for movie {movie_id} by user {user.id} from {old_rating} to {new_rating}")
        else:
            logger.info(f"Created new rating for movie {movie_id} by user {user.id} with rating {new_rating}")

        if old_rating is not None:
            update_suggestions_by_rate(user.id, movie_id, old_rating, subtract=True)

        update_suggestions_by_rate(user.id, movie_id, new_rating, subtract=False)

        logger.info(f"Suggestions updated for user {user.id} after rating movie {movie_id}")
        return Response(
            {"message": "Movie rated successfully and suggestions updated."},
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
        )
    except FileNotFoundError as e:
        logger.error(f"File not found error during suggestion update for user {user.id}, movie {movie_id}: {e}")
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        logger.error(f"Value error during suggestion update for user {user.id}, movie {movie_id}: {e}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error during movie rating or suggestion update for user {user.id}, movie {movie_id}: {e}")
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MovieListView(generics.ListAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access for listing
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["genres", "directors", "actors"]  # Assuming these are ManyToMany fields or similar
    search_fields = ["name", "description"]  # Search by movie name or description

    @swagger_auto_schema(
        operation_description="List all movies with optional search and filtering. Can search by name/description and filter by genre, director, or actor IDs.",
        operation_summary="List movies",
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search by movie name or description",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "genres",
                openapi.IN_QUERY,
                description="Filter by genre ID (e.g., ?genres=1,2)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "directors",
                openapi.IN_QUERY,
                description="Filter by director ID (e.g., ?directors=1)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "actors",
                openapi.IN_QUERY,
                description="Filter by actor ID (e.g., ?actors=1)",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: MovieSerializer(many=True),
            500: "Internal Server Error",
        },
        tags=["Movies"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MovieCommentViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ["list"]:
            return [AllowAny()]  # Anyone can list comments
        return [IsAuthenticated()]  # Only authenticated users can create, update, delete

    @swagger_auto_schema(
        operation_description="List comments for a specific movie.",
        operation_summary="List movie comments",
        manual_parameters=[
            openapi.Parameter(
                "movie_id",
                openapi.IN_QUERY,
                description="ID of the movie to retrieve comments for.",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={
            200: MovieReviewSerializer(many=True),
            400: "Bad Request",
            404: "Movie not found",
            500: "Internal Server Error",
        },
        tags=["Movies"],
    )
    def list(self, request):
        movie_id = request.query_params.get("movie_id")
        if not movie_id:
            return Response(
                {"error": "Movie ID is required as a query parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            movie = Movie.objects.get(id=movie_id)
            comments = MovieComment.objects.filter(movie=movie).order_by('-created_at') # Order by creation date
            serializer = MovieReviewSerializer(comments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Movie.DoesNotExist:
            return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error listing comments for movie {movie_id}: {e}")
            return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="Add a new comment to a movie.",
        operation_summary="Add movie comment",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["movie_id", "comment"],
            properties={
                "movie_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="ID of the movie to comment on."
                ),
                "comment": openapi.Schema(
                    type=openapi.TYPE_STRING, description="The comment text."
                ),
            },
        ),
        security=[{"Bearer": []}],
        responses={
            201: MovieReviewSerializer,
            400: "Bad Request",
            401: "Unauthorized",
            404: "Movie not found",
            409: "Conflict (User already commented on this movie)",
            500: "Internal Server Error",
        },
        tags=["Movies"],
    )
    def create(self, request):
        movie_id = request.data.get("movie_id")
        comment_text = request.data.get("comment")
        user = request.user

        if not movie_id or not comment_text:
            return Response(
                {"error": "Movie ID and comment are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

        if MovieComment.objects.filter(user=user, movie=movie).exists():
            return Response(
                {"error": "You have already commented on this movie. Use PUT to update."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            comment = MovieComment.objects.create(user=user, movie=movie, comment=comment_text)
            serializer = MovieReviewSerializer(comment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating comment for movie {movie_id} by user {user.id}: {e}")
            return Response(
                {"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Update an existing comment on a movie.",
        operation_summary="Update movie comment",
        manual_parameters=[
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="ID of the comment to update.",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["comment"],
            properties={
                "comment": openapi.Schema(
                    type=openapi.TYPE_STRING, description="The updated comment text."
                ),
            },
        ),
        security=[{"Bearer": []}],
        responses={
            200: MovieReviewSerializer,
            400: "Bad Request",
            401: "Unauthorized",
            403: "Permission Denied (Not your comment)",
            404: "Comment not found",
            500: "Internal Server Error",
        },
        tags=["Movies"],
    )
    def update(self, request, pk=None):
        comment_text = request.data.get("comment")
        user = request.user

        if not comment_text:
            return Response(
                {"error": "Comment text is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            comment = MovieComment.objects.get(id=pk)
        except MovieComment.DoesNotExist:
            return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)

        if comment.user != user:
            return Response(
                {"error": "You do not have permission to update this comment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            comment.comment = comment_text
            comment.save()
            serializer = MovieReviewSerializer(comment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error updating comment {pk} by user {user.id}: {e}")
            return Response(
                {"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Delete an existing comment on a movie.",
        operation_summary="Delete movie comment",
        manual_parameters=[
            openapi.Parameter(
                "pk",
                openapi.IN_PATH,
                description="ID of the comment to delete.",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        security=[{"Bearer": []}],
        responses={
            204: "No Content",
            401: "Unauthorized",
            403: "Permission Denied (Not your comment)",
            404: "Comment not found",
            500: "Internal Server Error",
        },
        tags=["Movies"],
    )
    def destroy(self, request, pk=None):
        user = request.user
        try:
            comment = MovieComment.objects.get(id=pk)
        except MovieComment.DoesNotExist:
            return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)

        if comment.user != user:
            return Response(
                {"error": "You do not have permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting comment {pk} by user {user.id}: {e}")
            return Response(
                {"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
