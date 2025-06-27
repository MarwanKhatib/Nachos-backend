"""Models package for the Nachos backend API.

This package contains all the database models used in the Nachos backend,
including models for users, movies, actors, directors, and other entities.
"""

from APIs.models.actor_model import Actor
from APIs.models.community_model import (
    MovieCommunity,
    UserGenre,
    UserSuggestionList,
    UserWatchedMovie,
    UserWatchlist,
)
from APIs.models.director_model import Director
from APIs.models.genre_model import Genre
from APIs.models.group_model import (
    Group,
    Post,
    UserComment,
    UserGroup,
    UserPost,
    UserReact,
)
from APIs.models.language_model import Language
from APIs.models.movie_actor_model import MovieActor
from APIs.models.movie_director_model import MovieDirector
from APIs.models.movie_genre_model import MovieGenre
from APIs.models.movie_model import Movie
from APIs.models.movie_producer_model import MovieProducer
from APIs.models.movie_writer_model import MovieWriter
from APIs.models.producer_model import Producer
from APIs.models.related_movie_model import RelatedMovie
from APIs.models.user_model import User
from APIs.models.writer_model import Writer
from APIs.models.movie_comment_model import MovieComment # Import new model

__all__ = [
    "User",
    "Genre",
    "Language",
    "Actor",
    "Director",
    "Writer",
    "Producer",
    "Movie",
    "RelatedMovie",
    "MovieActor",
    "MovieDirector",
    "MovieWriter",
    "MovieProducer",
    "MovieGenre",
    "UserGenre",
    "MovieCommunity",
    "UserWatchedMovie",
    "UserWatchlist",
    "UserSuggestionList",
    "Group",
    "UserGroup",
    "Post",
    "UserPost",
    "UserReact",
    "UserComment",
    "MovieComment", # Add to __all__
]
