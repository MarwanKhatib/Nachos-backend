import os
from django.conf import settings
from APIs.models import RelatedMovie, UserSuggestionList
from django.db import transaction # Import transaction for atomic operations

def update_suggestions_by_rate(user_id, movie_id, rating, subtract=False):
    """
    Update movie suggestions based on user's movie rating.
    Uses bulk operations for efficiency.
    """
    # Step 1: Construct the file path for the rating
    file_name = f"{rating}.txt"
    file_path = os.path.join(settings.BASE_DIR, 'APIs/utils', file_name)

    # Step 2: Check if the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File for rating {rating} not found.")

    # Step 3: Read the points from the file
    with open(file_path, 'r') as file:
        points_list = [int(line.strip()) for line in file if line.strip().isdigit()]

    # Step 4: Get related movies for the given movie_id
    related_movies = RelatedMovie.objects.filter(movie_id=movie_id).order_by('priority') # type: ignore

    # Step 5: Ensure the number of points matches the number of related movies
    if len(points_list) < len(related_movies):
        raise ValueError("Not enough points in the file for the number of related movies.")

    # Step 6: Update the total field in UserSuggestionList for the user
    with transaction.atomic():  # type: ignore
        # Get existing suggestions for the user and related movies
        related_movie_ids = [rm.related_id for rm in related_movies]
        existing_suggestions_queryset = UserSuggestionList.objects.filter(  # type: ignore
            user_id=user_id, movie_id__in=related_movie_ids
        )
        # Create a dictionary for efficient lookup by movie_id
        existing_suggestions = {
            suggestion.movie_id: suggestion for suggestion in existing_suggestions_queryset
        }

        suggestions_to_create = []
        suggestions_to_update = []

        for i, related_movie in enumerate(related_movies):
            point = points_list[i]
            movie_id_current = related_movie.related_id

            if movie_id_current in existing_suggestions:
                suggestion = existing_suggestions[movie_id_current]
                if subtract:
                    suggestion.total -= point
                else:
                    suggestion.total += point
                suggestions_to_update.append(suggestion)
            else:
                # Only create if it doesn't exist
                new_total = -point if subtract else point
                suggestions_to_create.append(
                    UserSuggestionList(
                        user_id=user_id,
                        movie_id=movie_id_current,
                        total=new_total,
                        is_watched=False,
                    )
                )

        if suggestions_to_create:
            UserSuggestionList.objects.bulk_create(suggestions_to_create)  # type: ignore

        if suggestions_to_update:
            UserSuggestionList.objects.bulk_update(suggestions_to_update, ["total"])  # type: ignore
