"""
This module contains serializers for the Nachos backend API.
It includes serializers for user management, movie operations, and group functionality.
"""

from .group_serializers import (
    BlockUserSerializer,
    CommentPostSerializer,
    CreateGroupSerializer,
    EditCommentSerializer,
    JoinGroupSerializer,
    UnblockUserSerializer,
    WritePostSerializer,
)
from .movie_serializers import (
    AddToWatchlistSerializer,
    MovieCommentSerializer,
    MovieInfosSerializer,
    MovieSerializer,
    PairStructuresSerializer,
    RateMovieSerializer,
    WatchlistItemSerializer,
)
from .user_serializers import (
    CustomTokenObtainPairSerializer,
    RegisterUserSerializer,
    SelectGenresSerializer,
    UserGenresSerializer,
    VerifyEmailSerializer,
)

__all__ = [
    "RegisterUserSerializer",
    "VerifyEmailSerializer",
    "CustomTokenObtainPairSerializer",
    "UserGenresSerializer",
    "SelectGenresSerializer",
    "PairStructuresSerializer",
    "MovieSerializer",
    "MovieInfosSerializer",
    "WatchlistItemSerializer",
    "RateMovieSerializer",
    "MovieCommentSerializer",
    "CreateGroupSerializer",
    "JoinGroupSerializer",
    "BlockUserSerializer",
    "UnblockUserSerializer",
    "WritePostSerializer",
    "CommentPostSerializer",
    "EditCommentSerializer",
    "AddToWatchlistSerializer",
]
