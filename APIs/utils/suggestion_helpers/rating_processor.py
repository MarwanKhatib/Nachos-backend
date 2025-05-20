import os
from django.conf import settings
from APIs.models import RelatedMovie, UserSuggestionList

def update_suggestions_by_rate(user_id, movie_id, rating, subtract=False):
    """
    Update movie suggestions based on user's movie rating.
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
    related_movies = RelatedMovie.objects.filter(movie_id=movie_id).order_by('priority')

    # Step 5: Ensure the number of points matches the number of related movies
    if len(points_list) < len(related_movies):
        raise ValueError("Not enough points in the file for the number of related movies.")

    # Step 6: Update the total field in UserSuggestionList for the user
    for i, related_movie in enumerate(related_movies):
        point = points_list[i]
        suggestion, _ = UserSuggestionList.objects.get_or_create(
            user_id=user_id,
            movie_id=related_movie.related_id,
            defaults={"total": 0, "is_watched": False}
        )

        if subtract:
            suggestion.total -= point
        else:
            suggestion.total += point

        suggestion.save()