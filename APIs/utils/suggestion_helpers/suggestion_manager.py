from APIs.models import Movie, MovieGenre, UserGenre, UserSuggestionList

from .genre_calculator import genres_delta


def create_initial_movie_suggestions(user):
    """
    Create initial movie suggestions for a new user.
    """
    movies = Movie.objects.all()
    for movie in movies:
        suggestion = UserSuggestionList(
            user=user, movie=movie, total=0, is_watched=False
        )
        suggestion.save()


def update_suggestions(user_id, genre_ids):
    """
    Update movie suggestions based on user's genre preferences, appending new genres.
    """
    # Get the user's existing genre IDs
    existing_genres = UserGenre.objects.filter(user_id=user_id).values_list(
        "genre_id", flat=True
    )
    existing_genre_ids = list(existing_genres)

    # Combine the existing genre IDs with the new genre IDs, removing duplicates
    combined_genre_ids = list(set(existing_genre_ids + genre_ids))

    # Prefetch MovieGenre objects for all suggestions
    user_suggestions = UserSuggestionList.objects.filter(
        user_id=user_id
    ).prefetch_related("movie__moviegenre_set")

    # read old genres and adjust points
    user_old_genres = UserGenre.objects.filter(user_id=user_id)
    for suggestion in user_suggestions:
        cur_suggestion = suggestion.movie.moviegenre_set.all()
        suggestion.total -= genres_delta(user_old_genres, cur_suggestion)
        suggestion.save()

    # clear old genres and add new ones
    UserGenre.objects.filter(user_id=user_id).delete()
    for genre_id in combined_genre_ids:
        UserGenre.objects.create(user_id=user_id, genre_id=genre_id)

    # recalculate points based on new genres
    for suggestion in user_suggestions:
        cur_suggestion = suggestion.movie.moviegenre_set.all()
        suggestion.total = genres_delta(combined_genre_ids, list(cur_suggestion))
        suggestion.save()
