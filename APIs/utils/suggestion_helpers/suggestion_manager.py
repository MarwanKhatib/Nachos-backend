from APIs.models import Movie, MovieGenre, UserGenre, UserSuggestionList, User
from django.db import transaction
from .genre_calculator import genres_delta


def create_initial_movie_suggestions(user):
    """
    Create initial movie suggestions for a new user using bulk creation.
    """
    movies = Movie.objects.all() # type: ignore
    suggestions_to_create = []
    for movie in movies:
        suggestions_to_create.append(
            UserSuggestionList(user=user, movie=movie, total=0, is_watched=False)
        )
    UserSuggestionList.objects.bulk_create(suggestions_to_create) # type: ignore


def update_suggestions(user_id, genre_ids):
    """
    Update movie suggestions based on user's genre preferences, appending new genres.
    Uses bulk operations for efficiency.
    """
    with transaction.atomic(): # type: ignore
        user = User.objects.get(id=user_id) # type: ignore

        # Get the user's existing genre IDs
        existing_genres = UserGenre.objects.filter(user=user).values_list( # type: ignore
            "genre_id", flat=True
        )
        existing_genre_ids = list(existing_genres)

        # Combine the existing genre IDs with the new genre IDs, removing duplicates
        combined_genre_ids = list(set(existing_genre_ids + genre_ids))

        # Prefetch MovieGenre objects for all suggestions
        user_suggestions = UserSuggestionList.objects.filter( # type: ignore
            user=user
        ).prefetch_related("movie__moviegenre_set")

        # Calculate and update points for existing suggestions based on old genres
        # This part still requires iterating, but we'll collect updates for bulk_update
        suggestions_to_update = []
        user_old_genres_objects = UserGenre.objects.filter(user=user) # type: ignore # Get objects for genres_delta
        for suggestion in user_suggestions:
            cur_movie_genres = suggestion.movie.moviegenre_set.all()
            # Subtract points based on old genres
            old_delta = genres_delta(user_old_genres_objects, cur_movie_genres)
            suggestion.total -= old_delta
            suggestions_to_update.append(suggestion)
        
        # Perform bulk update for subtracting old points
        if suggestions_to_update:
            UserSuggestionList.objects.bulk_update(suggestions_to_update, ['total']) # type: ignore

        # Clear old genres and add new ones using bulk_create
        UserGenre.objects.filter(user=user).delete() # type: ignore
        new_user_genres = []
        for genre_id in combined_genre_ids:
            new_user_genres.append(UserGenre(user=user, genre_id=genre_id))
        UserGenre.objects.bulk_create(new_user_genres) # type: ignore

        # Recalculate and update points based on new combined genres
        # This part still requires iterating, but we'll collect updates for bulk_update
        suggestions_to_update_final = []
        # Re-fetch user_suggestions if the previous prefetch_related might be stale due to genre changes
        # Or ensure genres_delta can work with just IDs if that's more efficient
        # For now, assuming genres_delta can work with combined_genre_ids directly
        
        # Re-fetch user_suggestions to ensure they are up-to-date after genre changes
        user_suggestions_re_fetched = UserSuggestionList.objects.filter( # type: ignore
            user=user
        ).prefetch_related("movie__moviegenre_set")

        for suggestion in user_suggestions_re_fetched:
            cur_movie_genres = suggestion.movie.moviegenre_set.all()
            # Add points based on new combined genres
            new_delta = genres_delta(combined_genre_ids, list(cur_movie_genres))
            suggestion.total = new_delta # Set to new total, not add to existing
            suggestions_to_update_final.append(suggestion)
        
        # Perform final bulk update for new points
        if suggestions_to_update_final:
            UserSuggestionList.objects.bulk_update(suggestions_to_update_final, ['total']) # type: ignore
