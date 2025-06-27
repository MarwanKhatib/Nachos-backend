import os
from django.conf import settings
from APIs.models.related_movie_model import RelatedMovie
from APIs.models.community_model import UserMovieSuggestion, UserGenre
from APIs.models.movie_model import Movie
from APIs.models.movie_genre_model import MovieGenre
from django.db import transaction
from APIs.utils.suggestion_helpers.suggestion_manager import update_suggestions
from APIs.utils.suggestion_helpers.genre_calculator import genres_delta # Import genres_delta

def update_suggestions_by_rate(user_id, movie_id, rating, subtract=False):
    """
    Update movie suggestions based on user's movie rating.
    This function will mark the rated movie as watched and adjust the suggestion scores
    of other movies based on the rated movie's genres and the given rating.
    """
    with transaction.atomic(): # type: ignore
        # 1. Mark the rated movie as watched
        user_movie_suggestion, created = UserMovieSuggestion.objects.get_or_create( # type: ignore
            user_id=user_id,
            movie_id=movie_id,
            defaults={'total': 0, 'is_watched': True}
        )
        if not created:
            user_movie_suggestion.is_watched = True
            user_movie_suggestion.save()

        # 2. Get genres of the rated movie
        rated_movie_genres = MovieGenre.objects.filter(movie_id=movie_id).values_list('genre_id', flat=True) # type: ignore
        rated_movie_genre_ids = list(rated_movie_genres)

        # 3. Adjust suggestion scores for other unwatched movies based on the rating
        # Get all unwatched movie suggestions for the user, excluding the just-rated movie
        other_movie_suggestions = UserMovieSuggestion.objects.select_related('movie').filter( # type: ignore
            user_id=user_id,
            is_watched=False
        ).exclude(movie_id=movie_id)

        # Fetch all genres for the relevant movies in one go
        movie_ids_to_process = [s.movie_id for s in other_movie_suggestions]
        movie_genres_data = MovieGenre.objects.filter(movie_id__in=movie_ids_to_process).values('movie_id', 'genre_id') # type: ignore
        
        # Organize genres by movie_id for easy lookup
        movie_genres_map = {}
        for mg in movie_genres_data:
            movie_genres_map.setdefault(mg['movie_id'], []).append(mg['genre_id'])

        suggestions_to_update = []
        # Determine the influence factor based on the rating
        # Ratings above 2.5 (mid-point) will boost, below will penalize
        rating_influence_factor = (rating - 2.5) / 2.5 # Normalize to -1 to 1 range approximately

        for suggestion in other_movie_suggestions:
            current_movie_genre_ids = movie_genres_map.get(suggestion.movie_id, [])

            # Calculate genre similarity between the rated movie and the current movie
            # Use rated_movie_genre_ids as list1_input (user's "preference" for this calculation)
            # and current_movie_genre_ids as list2_input
            genre_similarity_score = genres_delta(rated_movie_genre_ids, current_movie_genre_ids)

            # Apply the influence of the rating to the suggestion's total score
            # The impact is proportional to the genre similarity and the rating influence factor
            # A higher genre_similarity_score means more impact
            # Apply the same multiplier as in update_suggestions for consistency
            impact = int(genre_similarity_score * rating_influence_factor * 10)

            suggestion.total += impact
            # Ensure total doesn't go below 0. Max cap can be added if scores grow too large.
            suggestion.total = max(0, suggestion.total)

            suggestions_to_update.append(suggestion)

        if suggestions_to_update:
            UserMovieSuggestion.objects.bulk_update(suggestions_to_update, ['total']) # type: ignore

        # Removed the full recalculation based on user's overall genre preferences
        # to improve performance on each movie rating. The full recalculation
        # will still occur when the user explicitly sets their preferred genres.
