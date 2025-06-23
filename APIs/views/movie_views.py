"""
Views for movie-related API endpoints.

This module contains view functions for handling movie-related API requests,
including retrieving movie details, managing watchlists, ratings and comments.
"""

import logging

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)

from APIs.models import (
    Actor,
    Director,
    Genre,
    Movie,
    MovieActor,
    MovieDirector,
    MovieGenre,
    MovieProducer,
    MovieWriter,
    Producer,
    User,
    UserGenre,
    UserSuggestionList,
    UserWatchedMovie,
    UserWatchlist,
    Writer,
)
from APIs.models.movie_writer_model import MovieWriter
from APIs.serializers import (
    AddToWatchlistSerializer,
    MovieCommentSerializer,
    MovieInfosSerializer,
    MovieSerializer,
    PairStructuresSerializer,
    RateMovieSerializer,
    SelectGenresSerializer,
    WatchlistItemSerializer,
)
from APIs.utils.suggestion_helpers import update_suggestions, update_suggestions_by_rate


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
def get_movie(request, movie_id=None):
    if movie_id is None:
        movie_id = 1  # Use a default movie_id for testing
    logger.info(f"Attempting to retrieve movie with ID: {movie_id}")
    try:
        movie = Movie.objects.get(id=movie_id)  # type: ignore
        logger.info(f"Successfully retrieved movie: {movie.name}")
    except Movie.DoesNotExist:  # type: ignore
        logger.warning(f"Movie with ID {movie_id} not found.")
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error retrieving movie {movie_id}: {e}", exc_info=True)
        return Response(
            {"error": "Internal server error."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    actors = Actor.objects.filter(  # type: ignore
        id__in=MovieActor.objects.filter(movie_id=movie.id).values_list(  # type: ignore
            "actor_id", flat=True
        )
    )
    writers = Writer.objects.filter(  # type: ignore
        id__in=MovieWriter.objects.filter(movie_id=movie.id).values_list(  # type: ignore
            "writer_id", flat=True
        )
    )
    producers = Producer.objects.filter(  # type: ignore
        id__in=MovieProducer.objects.filter(movie_id=movie.id).values_list(  # type: ignore
            "producer_id", flat=True
        )
    )
    directors = Director.objects.filter(  # type: ignore
        id__in=MovieDirector.objects.filter(movie_id=movie.id).values_list(  # type: ignore
            "director_id", flat=True
        )
    )
    genres = Genre.objects.filter(  # type: ignore
        id__in=MovieGenre.objects.filter(movie_id=movie.id).values_list(  # type: ignore
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
    operation_description="Add movie to user watch list",
    operation_summary="Add movie to watch list",
    request_body=AddToWatchlistSerializer,
    security=[{"Bearer": []}],  # Indicate JWT authentication
    responses={
        201: openapi.Response(
            "Created",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING, description="Success message"
                    )
                },
            ),
        ),
        400: openapi.Response(
            "Bad Request",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Error message when movie is already in watchlist",
                    ),
                    "error": openapi.Schema(
                        type=openapi.TYPE_OBJECT, description="Validation errors"
                    ),
                },
            ),
        ),
        404: openapi.Response(
            "Not Found",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Error message when movie not found",
                    )
                },
            ),
        ),
        401: openapi.Response(
            "Unauthorized",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Error message when user is not authenticated",
                    )
                },
            ),
        ),
    },
    tags=["Movies"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_watchlist(request):
    logger.info(f"User {request.user.id} attempting to add movie to watchlist.")
    serializer = AddToWatchlistSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(f"Invalid data for add_to_watchlist: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    movie_id = serializer.validated_data.get("movie_id")
    if movie_id is None:
        movie_id = 1 # Default for testing, but should be handled by serializer validation
        logger.warning("movie_id not provided in request, using default for testing.")

    user = request.user

    try:
        movie = Movie.objects.get(id=movie_id) # type: ignore
    except Movie.DoesNotExist: # type: ignore
        logger.warning(f"Movie with ID {movie_id} not found for watchlist.")
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error checking movie existence for watchlist: {e}", exc_info=True)
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if UserWatchlist.objects.filter(user=user, movie=movie).exists(): # type: ignore
        logger.info(f"Movie {movie_id} already in watchlist for user {user.id}.")
        return Response(
            {"message": "Movie is already in the watchlist."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        UserWatchlist.objects.create(user=user, movie=movie) # type: ignore
        logger.info(f"Movie {movie_id} added to watchlist for user {user.id}.")
        return Response(
            {"message": "Movie added to watchlist successfully."},
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        logger.error(f"Error adding movie {movie_id} to watchlist for user {user.id}: {e}", exc_info=True)
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method="post",
    operation_description="Select genres for user",
    operation_summary="Select genres for user",
    request_body=SelectGenresSerializer,
    security=[{"Bearer": []}],
    responses={
        200: openapi.Response(
            "Success",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Genre preferences updated successfully.",
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
        401: openapi.Response(
            "Unauthorized",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Error message when user is not authenticated",
                    )
                },
            ),
        ),
    },
    tags=["Movies"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def select_genres(request):
    logger.info(f"User {request.user.id} attempting to select genres.")
    serializer = SelectGenresSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(f"Invalid data for select_genres: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    genre_ids = serializer.validated_data["genre_ids"]

    try:
        update_suggestions(user.id, genre_ids)
        logger.info(f"Genre preferences updated successfully for user {user.id}.")
        return Response(
            {"message": "Genre preferences updated successfully."},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        logger.error(f"Error updating genre suggestions for user {user.id}: {e}", exc_info=True)
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Getting User Genre
@swagger_auto_schema(
    method="get",
    operation_description="Get genres selected by the authenticated user",
    operation_summary="Get user genres",
    security=[{"Bearer": []}],
    responses={
        200: openapi.Response(
            "Success",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "genres": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING),
                        description="List of genre names",
                    )
                },
            ),
        ),
        401: openapi.Response(
            "Unauthorized",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Error message when user is not authenticated",
                    )
                },
            ),
        ),
    },
    tags=["Movies"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_genres(request):
    user = request.user
    logger.info(f"User {user.id} attempting to retrieve selected genres.")
    try:
        user_genres = UserGenre.objects.filter(user_id=user).select_related("genre") # type: ignore
        genre_names = [ug.genre.name for ug in user_genres]
        logger.info(f"Successfully retrieved genres for user {user.id}.")
        return Response({"genres": genre_names}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error retrieving user genres for user {user.id}: {e}", exc_info=True)
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Getting top 10 Suggestion for user
@swagger_auto_schema(
    method="get",
    operation_description="Get top 10 movie suggestions for the authenticated user",
    operation_summary="Get top 10 movie suggestions",
    security=[{"Bearer": []}],
    responses={
        200: openapi.Response(
            "Success",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "movie_ids": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_INTEGER),
                        description="List of movie IDs",
                    )
                },
            ),
        ),
        401: openapi.Response(
            "Unauthorized",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Error message when user is not authenticated",
                    )
                },
            ),
        ),
    },
    tags=["Movies"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_top_10_suggestions(request):
    user = request.user
    logger.info(f"User {user.id} attempting to retrieve top 10 movie suggestions.")
    try:
        suggestions = UserSuggestionList.objects.filter( # type: ignore
            user_id=user, is_watched=False
        ).order_by("-total")

        if not suggestions.exists():
            logger.info(f"No unwatched suggestions for user {user.id}, resetting watched status.")
            UserSuggestionList.objects.filter(user_id=user).update(is_watched=False) # type: ignore
            suggestions = UserSuggestionList.objects.filter( # type: ignore
                user_id=user, is_watched=False
            ).order_by("-total")

        suggestions = suggestions[:10]
        for suggestion in suggestions:
            suggestion.is_watched = True
            suggestion.save()
        
        movie_ids = [s.movie_id for s in suggestions]
        logger.info(f"Successfully retrieved {len(movie_ids)} suggestions for user {user.id}.")
        return Response({"movie_ids": movie_ids}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error retrieving top 10 suggestions for user {user.id}: {e}", exc_info=True)
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# get user watchlist API
@swagger_auto_schema(
    method="get",
    operation_description="Get the movie watchlist for the authenticated user",
    operation_summary="Get user watchlist",
    security=[{"Bearer": []}],
    responses={
        200: openapi.Response(
            "Success",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "movie_ids": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_INTEGER),
                        description="List of movie IDs in the watchlist",
                    )
                },
            ),
        ),
        401: openapi.Response(
            "Unauthorized",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Error message when user is not authenticated",
                    )
                },
            ),
        ),
    },
    tags=["Movies"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_watchlist(request):
    user = request.user
    logger.info(f"User {user.id} attempting to retrieve watchlist.")
    try:
        watchlist_movie_ids = UserWatchlist.objects.filter(user=user).values_list( # type: ignore
            "movie_id", flat=True
        )
        logger.info(f"Successfully retrieved watchlist for user {user.id}.")
        return Response({"movie_ids": list(watchlist_movie_ids)}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error retrieving watchlist for user {user.id}: {e}", exc_info=True)
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method="post",
    operation_description="Remove a movie from the authenticated user's watchlist",
    operation_summary="Remove movie from watchlist",
    security=[{"Bearer": []}],
    request_body=WatchlistItemSerializer,
    responses={
        200: openapi.Response(
            "Success",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Movie removed from watchlist successfully.",
                    )
                },
            ),
        ),
        400: openapi.Response(
            "Bad Request",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Movie is not in the watchlist.",
                    )
                },
            ),
        ),
        404: openapi.Response(
            "Not Found",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Movie not found.",
                    )
                },
            ),
        ),
        401: openapi.Response(
            "Unauthorized",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="User not authenticated.",
                    )
                },
            ),
        ),
    },
    tags=["Movies"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def remove_from_watchlist(request):
    logger.info(f"User {request.user.id} attempting to remove movie from watchlist.")
    serializer = WatchlistItemSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(f"Invalid data for remove_from_watchlist: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    movie_id = serializer.validated_data["movie_id"]
    user = request.user

    try:
        movie = Movie.objects.get(id=movie_id)  # type: ignore
    except Movie.DoesNotExist:  # type: ignore
        logger.warning(f"Movie with ID {movie_id} not found for watchlist removal.")
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(
            f"Error checking movie existence for watchlist removal: {e}", exc_info=True
        )
        return Response(
            {"error": "Internal server error."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        watchlist_entry = UserWatchlist.objects.get(
            user=user, movie=movie
        )  # type: ignore
    except UserWatchlist.DoesNotExist:  # type: ignore
        logger.info(f"Movie {movie_id} not in watchlist for user {user.id}.")
        return Response(
            {"message": "Movie is not in the watchlist."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error(f"Error checking watchlist entry for removal: {e}", exc_info=True)
        return Response(
            {"error": "Internal server error."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        watchlist_entry.delete()
        logger.info(f"Movie {movie_id} removed from watchlist for user {user.id}.")
        return Response(
            {"message": "Movie removed from watchlist successfully."},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        logger.error(
            f"Error removing movie {movie_id} from watchlist for user {user.id}: {e}",
            exc_info=True,
        )
        return Response(
            {"error": "Internal server error."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="post",
    operation_description="Rate a movie and update suggestions",
    operation_summary="Rate a movie",
    security=[{"Bearer": []}],
    request_body=RateMovieSerializer,
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
def rate_movie(request):
    logger.info(f"User {request.user.id} attempting to rate movie.")
    serializer = RateMovieSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(f"Invalid data for rate_movie: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    movie_id = serializer.validated_data["movie_id"]
    new_rating = serializer.validated_data["rate"]

    try:
        movie = Movie.objects.get(id=movie_id) # type: ignore
    except Movie.DoesNotExist: # type: ignore
        logger.warning(f"Movie with ID {movie_id} not found for rating.")
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error checking movie existence for rating: {e}", exc_info=True)
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        watched_movie, created = UserWatchedMovie.objects.get_or_create( # type: ignore
            user=user,
            movie=movie,
            defaults={"rate": new_rating},
        )

        old_rating = None
        if not created:
            old_rating = watched_movie.rate
            watched_movie.rate = new_rating
            watched_movie.save()
            logger.info(f"Updated rating for movie {movie_id} by user {user.id} from {old_rating} to {new_rating}.")
        else:
            logger.info(f"Created new rating for movie {movie_id} by user {user.id} with rating {new_rating}.")

        if old_rating is not None:
            update_suggestions_by_rate(user.id, movie_id, old_rating, subtract=True)

        update_suggestions_by_rate(user.id, movie_id, new_rating, subtract=False)
        
        logger.info(f"Suggestions updated for user {user.id} after rating movie {movie_id}.")
        return Response(
            {"message": "Movie rated successfully and suggestions updated."},
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
        )
    except FileNotFoundError as e:
        logger.error(f"File not found error during suggestion update for user {user.id}, movie {movie_id}: {e}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        logger.error(f"Value error during suggestion update for user {user.id}, movie {movie_id}: {e}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error during movie rating or suggestion update for user {user.id}, movie {movie_id}: {e}", exc_info=True)
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
