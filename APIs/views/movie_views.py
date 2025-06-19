"""
Views for movie-related API endpoints.

This module contains view functions for handling movie-related API requests,
including retrieving movie details, managing watchlists, ratings and comments.
"""

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

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
        return Response(serializer.data)
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
    # Validate input data
    serializer = AddToWatchlistSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Extract validated data
    if "movie_id" in request.data:
        movie_id = serializer.validated_data["movie_id"]
    else:
        movie_id = 1  # Use a default movie_id for testing
    user = request.user

    # Check if the movie exist
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

    # Check if the movie is already in the watchlist
    if UserWatchlist.objects.filter(user=user, movie=movie).exists():
        return Response(
            {"message": "Movie is already in the watchlist."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Add the movie to the watchlist
    UserWatchlist.objects.create(user=user, movie=movie)
    return Response(
        {"message": "Movie added to watchlist successfully."},
        status=status.HTTP_201_CREATED,
    )


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
    serializer = SelectGenresSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    genre_ids = serializer.validated_data["genre_ids"]

    update_suggestions(user.id, genre_ids)

    return Response(
        {"message": "Genre preferences updated successfully."},
        status=status.HTTP_200_OK,
    )


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

    user_genres = UserGenre.objects.filter(user_id=user).select_related("genre")
    genre_names = [ug.genre.name for ug in user_genres]

    return Response({"genres": genre_names}, status=status.HTTP_200_OK)


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

    suggestions = UserSuggestionList.objects.filter(
        user_id=user, is_watched=False
    ).order_by("-total")

    if not suggestions.exists():
        UserSuggestionList.objects.filter(user_id=user).update(is_watched=False)
        suggestions = UserSuggestionList.objects.filter(
            user_id=user, is_watched=False
        ).order_by("-total")

    suggestions = suggestions[:10]
    for suggestion in suggestions:
        suggestion.is_watched = True
        suggestion.save()

    movie_ids = [s.movie_id for s in suggestions]
    return Response({"movie_ids": movie_ids}, status=status.HTTP_200_OK)


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

    # Get all movie IDs in the user's watchlist
    watchlist_movie_ids = UserWatchlist.objects.filter(user=user).values_list(
        "movie_id", flat=True
    )

    # Convert the QuerySet to a list and return it
    return Response({"movie_ids": list(watchlist_movie_ids)}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="post",
    operation_description="Remove a movie from the authenticated user's watchlist",
    operation_summary="Remove movie from watchlist",
    security=[{"Bearer": []}],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["movie_id"],
        properties={
            "movie_id": openapi.Schema(
                type=openapi.TYPE_INTEGER, description="ID of the movie to remove"
            )
        },
    ),
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
    # Validate input data
    serializer = WatchlistItemSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Extract validated data
    movie_id = serializer.validated_data["movie_id"]

    # Check if the user and movie exist
    user = request.user
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

    # Check if the movie is in the watchlist
    try:
        watchlist_entry = UserWatchlist.objects.get(user=user, movie=movie)
    except UserWatchlist.DoesNotExist:
        return Response(
            {"message": "Movie is not in the watchlist."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Delete the movie from the watchlist
    watchlist_entry.delete()
    return Response(
        {"message": "Movie removed from watchlist successfully."},
        status=status.HTTP_200_OK,
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
    # Step 1: Validate input data
    serializer = RateMovieSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Step 2: Extract validated data
    user = request.user
    movie_id = serializer.validated_data["movie_id"]
    new_rating = serializer.validated_data["rating"]

    # Step 3: Check if the user and movie exist
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

    # Step 4: Get or create the rating in UserWatchedMovie
    watched_movie, created = UserWatchedMovie.objects.get_or_create(
        user=user,
        movie=movie,
        defaults={"rate": new_rating},  # Default value if creating a new entry
    )

    # Step 5: Handle old rating (if it exists)
    old_rating = None
    if not created:
        old_rating = watched_movie.rate  # Save the old rating
        watched_movie.rate = new_rating  # Update to the new rating
        watched_movie.save()

    # Step 6: Update suggestions based on the ratings
    try:
        # Remove old points (if applicable)
        if old_rating is not None:
            update_suggestions_by_rate(user.id, movie_id, old_rating, subtract=True)

        # Add new points
        update_suggestions_by_rate(user.id, movie_id, new_rating, subtract=False)
    except FileNotFoundError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Step 7: Return success response
    return Response(
        {"message": "Movie rated successfully and suggestions updated."},
        status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
    )
