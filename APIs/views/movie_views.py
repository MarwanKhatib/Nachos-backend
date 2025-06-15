"""
Views for movie-related API endpoints.

This module contains view functions for handling movie-related API requests,
including retrieving movie details, managing watchlists, ratings and comments.
"""

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view
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
    Writer,
)
from APIs.models.movie_writer_model import MovieWriter
from APIs.serializers.movie_serializers import (
    MovieCommentSerializer,
    MovieInfosSerializer,
    MovieSerializer,
    PairStructuresSerializer,
    RateMovieSerializer,
    WatchlistItemSerializer,
)


# Getting all Movie Details
@swagger_auto_schema(
    method='get',
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
