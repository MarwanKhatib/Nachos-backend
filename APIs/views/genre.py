"""
Views for genre-related API endpoints.

This module contains view functions and class-based views for handling genre-related API requests,
including retrieving all genres, and managing user-specific genre preferences.
"""

import logging

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

from APIs.models.genre_model import Genre
from APIs.models.community_model import UserGenre
from typing import cast

from APIs.serializers.user_serializers import SelectGenresSerializer
from APIs.utils.suggestion_helpers import update_suggestions


@swagger_auto_schema(
    method="get",
    operation_description="Get all genres",
    operation_summary="Get all genres",
    responses={
        200: openapi.Response(
            "Success",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "genres": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Genre ID"),
                                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Genre name"),
                            },
                        ),
                        description="List of all genres with their ID and name",
                    )
                },
            ),
        ),
        500: openapi.Response(
            "Internal Server Error",
            openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Error message when there is a server error",
                    )
                },
            ),
        ),
    },
    tags=["Genres"],
)
@api_view(["GET"])
def get_all_genres(request):
    path = request.path
    user_id = request.user.id if request.user.is_authenticated else 'anonymous'
    logger.info(f"Request by user {user_id} to {path} for all genres.")
    try:
        genres = Genre.objects.all()  # type: ignore
        genre_data = [{"id": genre.id, "name": genre.name} for genre in genres]
        logger.info(f"Successfully retrieved {len(genre_data)} genres for user {user_id} to {path}.")
        return Response({"genres": genre_data}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error retrieving all genres for user {user_id} to {path}: {e}", exc_info=True)
        return Response(
            {"error": "Internal server error."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class UserGenresView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
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
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Genre ID"),
                                    "name": openapi.Schema(type=openapi.TYPE_STRING, description="Genre name"),
                                },
                            ),
                            description="List of genres selected by the user with their ID and name",
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
            500: openapi.Response(
                "Internal Server Error",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Error message when there is a server error",
                        )
                    },
                ),
            ),
        },
        tags=["Genres"],
    )
    def get(self, request):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for retrieving selected genres.")
        try:
            user_genres = UserGenre.objects.filter(user_id=user).select_related("genre")  # type: ignore
            genre_data = [{"id": ug.genre.id, "name": ug.genre.name} for ug in user_genres]
            logger.info(f"Successfully retrieved genres for user {user.id} to {path}.")
            return Response({"genres": genre_data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving user genres for user {user.id} to {path}: {e}", exc_info=True)
            return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
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
            500: openapi.Response(
                "Internal Server Error",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Error message when there is a server error",
                        )
                    },
                ),
            ),
        },
        tags=["Genres"],
    )
    def post(self, request):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for selecting genres.")
        serializer = SelectGenresSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid data for select_genres by user {user.id} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        genre_ids = cast(dict, serializer.validated_data)["genre_ids"]

        try:
            update_suggestions(user.id, genre_ids)
            logger.info(f"Genre preferences updated successfully for user {user.id} to {path}.")
            return Response(
                {"message": "Genre preferences updated successfully."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error updating genre suggestions for user {user.id} to {path}: {e}", exc_info=True)
            return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="Remove genres from user's selected genres",
        operation_summary="Remove user genres",
        request_body=SelectGenresSerializer, # Reusing serializer as it takes a list of IDs
        security=[{"Bearer": []}],
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Genres removed successfully.",
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
            404: openapi.Response(
                "Not Found",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="One or more genres not found for the user.",
                        )
                    },
                ),
            ),
            500: openapi.Response(
                "Internal Server Error",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Error message when there is a server error",
                        )
                    },
                ),
            ),
        },
        tags=["Genres"],
    )
    def delete(self, request):
        user = request.user
        path = request.path
        logger.info(f"Request by user {user.id} to {path} for removing genres.")
        serializer = SelectGenresSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid data for remove_genres by user {user.id} to {path}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        genre_ids_to_remove = cast(dict, serializer.validated_data)["genre_ids"]

        try:
            # Filter for UserGenre objects that match the user and the provided genre_ids
            deleted_count, _ = UserGenre.objects.filter(
                user=user, genre_id__in=genre_ids_to_remove
            ).delete()

            if deleted_count == 0:
                logger.warning(f"No genres found to remove for user {user.id} with IDs: {genre_ids_to_remove} to {path}.")
                return Response(
                    {"message": "No matching genres found for removal or already removed."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            logger.info(f"Successfully removed {deleted_count} genres for user {user.id} to {path}.")
            return Response(
                {"message": "Genres removed successfully."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error removing genres for user {user.id} to {path}: {e}", exc_info=True)
            return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
