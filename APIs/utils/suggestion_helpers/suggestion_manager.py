from APIs.models.movie_model import Movie
from APIs.models.movie_genre_model import MovieGenre
from APIs.models.community_model import UserGenre, UserSuggestionList, UserMovieSuggestion # Import new model
from APIs.models.user_model import User
from django.db import transaction
from APIs.utils.suggestion_helpers.genre_calculator import genres_delta
import logging
import time

logger = logging.getLogger(__name__)


def create_initial_movie_suggestions(user):
    """
    Create initial movie suggestions for a new user using bulk creation.
    """
    movies = Movie.objects.all() # type: ignore
    suggestions_to_create = []
    for movie in movies:
        suggestions_to_create.append(
            UserMovieSuggestion(user=user, movie=movie, total=0, is_watched=False)
        )
    UserMovieSuggestion.objects.bulk_create(suggestions_to_create) # type: ignore
    # Ensure UserSuggestionList header exists for the user
    UserSuggestionList.objects.get_or_create(user=user) # type: ignore


def update_suggestions(user_id, genre_ids):
    """
    Update movie suggestions based on user's genre preferences, appending new genres.
    Uses bulk operations for efficiency.
    """
    start_time = time.time()
    logger.info(f"Starting update_suggestions for user {user_id}")

    with transaction.atomic(): # type: ignore
        user = User.objects.get(id=user_id) # type: ignore

        # Get the user's existing genre IDs
        existing_genres = UserGenre.objects.filter(user=user).values_list( # type: ignore
            "genre_id", flat=True
        )
        existing_genre_ids = list(existing_genres)

        # Combine the existing genre IDs with the new genre IDs, removing duplicates
        combined_genre_ids = list(set(existing_genre_ids + genre_ids))

        # Clear old genres and add new ones using bulk_create
        UserGenre.objects.filter(user=user).delete() # type: ignore
        new_user_genres = []
        for genre_id in combined_genre_ids:
            new_user_genres.append(UserGenre(user=user, genre_id=genre_id))
        UserGenre.objects.bulk_create(new_user_genres) # type: ignore

        # Fetch all user's movie suggestions
        user_movie_suggestions = UserMovieSuggestion.objects.filter( # type: ignore
            user=user
        ).prefetch_related("movie__moviegenre_set")

        suggestions_to_update = []
        for suggestion in user_movie_suggestions:
            cur_movie_genres = suggestion.movie.moviegenre_set.all()
            # Recalculate points based on new combined genres
            # genres_delta now returns a raw weighted sum. Apply a multiplier for impact.
            raw_genre_score = genres_delta(combined_genre_ids, list(cur_movie_genres))
            # A multiplier (e.g., 10 or 100) can be adjusted based on desired score range
            # and how much genre similarity should contribute to the total.
            # Let's use a multiplier of 10 for now.
            new_total = raw_genre_score * 10
            suggestion.total = new_total
            suggestions_to_update.append(suggestion)
        
        # Perform bulk update for new points
        if suggestions_to_update:
            UserMovieSuggestion.objects.bulk_update(suggestions_to_update, ['total']) # type: ignore
    
    end_time = time.time()
    logger.info(f"Finished update_suggestions for user {user_id} in {end_time - start_time:.2f} seconds.")
