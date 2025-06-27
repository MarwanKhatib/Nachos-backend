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
    MovieInfosSerializer,
    MovieSerializer,
    PairStructuresSerializer,
    RateMovieSerializer,
    WatchlistItemSerializer,
)
from .movie_review_serializer import MovieReviewSerializer # Import the new serializer
from .user_serializers import (
    CustomTokenObtainPairSerializer,
    RegisterUserSerializer,
    SelectGenresSerializer,
    UserGenresSerializer,
    VerifyEmailSerializer,
    RequestPasswordResetSerializer, # New serializer
    SetNewPasswordSerializer, # New serializer
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
    "MovieReviewSerializer", # Add the new serializer
    "CreateGroupSerializer",
    "JoinGroupSerializer",
    "BlockUserSerializer",
    "UnblockUserSerializer",
    "WritePostSerializer",
    "CommentPostSerializer",
    "EditCommentSerializer",
    "AddToWatchlistSerializer",
    "RequestPasswordResetSerializer", # Add to __all__
    "SetNewPasswordSerializer", # Add to __all__
]
