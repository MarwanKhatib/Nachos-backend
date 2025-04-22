from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.decorators import api_view
import os
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
# join movie community API
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User, Movie, UserWatchedMovie, MovieCommunity

from .models import * 
from .serializers import *

from django.http import HttpResponse

# Temp Hello World
def hello_world(request):
    return HttpResponse("Hello, world!")



# Registeration API
@api_view(['POST'])
def register_user(request):
    serializer = RegisterUserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "User registered successfully. Check your email for the verification code."},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Email Verfication API
@api_view(['POST'])
def verify_email(request):
    serializer = VerifyEmailSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        user = User.objects.filter(email=email).first()
        if user:
            user.is_active = True
            user.save()

            create_initial_movie_suggestions(user)

            return Response({"message": "Email verified successfully."}, status=status.HTTP_200_OK)
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Login API
@api_view(['POST'])
def custom_token_obtain_pair(request):
    serializer = TokenObtainPairSerializer(data=request.data)

    try:
        serializer.is_valid(raise_exception=True)
    except TokenError as e:
        raise InvalidToken(e.args[0])

    # Customize the response if needed
    data = serializer.validated_data
    data['user_id'] = serializer.user.id
    data['username'] = serializer.user.username
    data['email'] = serializer.user.email

    return Response(data)

# Refresh token API
@api_view(['POST'])
def custom_token_refresh(request):
    serializer = TokenRefreshSerializer(data=request.data)

    try:
        serializer.is_valid(raise_exception=True)
    except TokenError as e:
        raise InvalidToken(e.args[0])

    # Return the new access token
    return Response(serializer.validated_data)

# Genre Selection APIs
@api_view(['POST'])
def select_genres(request):
    serializer = SelectGenresSerializer(data=request.data)
    if serializer.is_valid():
        user_id = serializer.validated_data["user_id"]
        genre_ids = serializer.validated_data["genre_ids"]

        update_suggestions( user_id , genre_ids )

        return Response({"message": "Genre preferences updated successfully."}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Getting User Genre
@api_view(['GET'])
def get_user_genres(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    user_genres = UserGenre.objects.filter(user_id=user).select_related("genre")
    genre_names = [ug.genre.name for ug in user_genres]

    return Response({"genres": genre_names}, status=status.HTTP_200_OK)

# Getting top 10 Suggestion for user
@api_view(['GET'])
def get_top_10_suggestions(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    suggestions = UserSuggestionList.objects.filter(user_id=user, is_watched=False).order_by("-total")

    if not suggestions.exists():
        UserSuggestionList.objects.filter(user_id=user).update(is_watched=False)
        suggestions = UserSuggestionList.objects.filter(user_id=user, is_watched=False).order_by("-total")

    suggestions = suggestions[:10]
    for suggestion in suggestions:
        suggestion.is_watched = True
        suggestion.save()

    movie_ids = [s.movie_id for s in suggestions]
    return Response({"movie_ids": movie_ids}, status=status.HTTP_200_OK)

# Getting all Movie Details
@api_view(['GET'])
def get_movie(request, movie_id):
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

    actors = Actor.objects.filter(id__in=MovieActor.objects.filter(movie_id=movie.id).values_list('actor_id', flat=True))
    writers = Writer.objects.filter(id__in=MovieWriter.objects.filter(movie_id=movie.id).values_list('writer_id', flat=True))
    producers = Producer.objects.filter(id__in=MovieProducer.objects.filter(movie_id=movie.id).values_list('producer_id', flat=True))
    directors = Director.objects.filter(id__in=MovieDirector.objects.filter(movie_id=movie.id).values_list('director_id', flat=True))
    genres = Genre.objects.filter(id__in=MovieGenre.objects.filter(movie_id=movie.id).values_list('genre_id', flat=True))

    movie_data = {
        "name": movie.name,
        "description": movie.description,
        "trailer": movie.trailer,
        "poster": movie.poster,
        "language": movie.language.name,
        "actors": [actor.name for actor in actors],
        "writers": [writer.name for writer in writers],
        "producers": [producer.name for producer in producers],
        "directors": [director.name for director in directors],
        "genres": [genre.name for genre in genres],
    }

    serializer = MovieInfosSerializer(data=movie_data)
    if serializer.is_valid():
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# add movie to watchlist API
@api_view(['POST'])
def add_to_watchlist(request):
    # Validate input data
    serializer = WatchlistItemSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Extract validated data
    user_id = serializer.validated_data['user_id']
    movie_id = serializer.validated_data['movie_id']

    # Check if the user and movie exist
    try:
        user = User.objects.get(id=user_id)
        movie = Movie.objects.get(id=movie_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Movie.DoesNotExist:
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

    # Check if the movie is already in the watchlist
    if UserWatchlist.objects.filter(user=user, movie=movie).exists():
        return Response({"message": "Movie is already in the watchlist."}, status=status.HTTP_400_BAD_REQUEST)

    # Add the movie to the watchlist
    UserWatchlist.objects.create(user=user, movie=movie)
    return Response({"message": "Movie added to watchlist successfully."}, status=status.HTTP_201_CREATED)

# get user watchlist API
@api_view(['GET'])
def get_watchlist(request, user_id):
    # Check if the user exists
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    # Get all movie IDs in the user's watchlist
    watchlist_movie_ids = UserWatchlist.objects.filter(user=user).values_list('movie_id', flat=True)

    # Convert the QuerySet to a list and return it
    return Response({"movie_ids": list(watchlist_movie_ids)}, status=status.HTTP_200_OK)

# erase movie from a user watchlist API

@api_view(['POST'])
def remove_from_watchlist(request):
    # Validate input data
    serializer = WatchlistItemSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Extract validated data
    user_id = serializer.validated_data['user_id']
    movie_id = serializer.validated_data['movie_id']

    # Check if the user and movie exist
    try:
        user = User.objects.get(id=user_id)
        movie = Movie.objects.get(id=movie_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Movie.DoesNotExist:
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

    # Check if the movie is in the watchlist
    try:
        watchlist_entry = UserWatchlist.objects.get(user=user, movie=movie)
    except UserWatchlist.DoesNotExist:
        return Response({"message": "Movie is not in the watchlist."}, status=status.HTTP_400_BAD_REQUEST)

    # Delete the movie from the watchlist
    watchlist_entry.delete()
    return Response({"message": "Movie removed from watchlist successfully."}, status=status.HTTP_200_OK)

# rate a movie api
@api_view(['POST'])
def rate_movie(request):
    # Step 1: Validate input data
    serializer = RateMovieSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Step 2: Extract validated data
    user_id = serializer.validated_data['user_id']
    movie_id = serializer.validated_data['movie_id']
    new_rating = serializer.validated_data['rate']

    # Step 3: Check if the user and movie exist
    try:
        user = User.objects.get(id=user_id)
        movie = Movie.objects.get(id=movie_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Movie.DoesNotExist:
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

    # Step 4: Get or create the rating in UserWatchedMovie
    watched_movie, created = UserWatchedMovie.objects.get_or_create(
        user=user,
        movie=movie,
        defaults={"rate": new_rating}  # Default value if creating a new entry
    )

    # Step 5: Handle old rating (if it exists)
    old_rating = None
    if not created:
        old_rating = watched_movie.rate  # Save the old rating
        watched_movie.rate = new_rating  # Update to the new rating
        watched_movie.save()

    # Step 6: Update suggestions based on the ratings
    try:
        # Remove old points (if applicable)
        if old_rating is not None:
            update_suggestions_by_rate(user_id, movie_id, old_rating, subtract=True)

        # Add new points
        update_suggestions_by_rate(user_id, movie_id, new_rating, subtract=False)
    except FileNotFoundError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Step 7: Return success response
    return Response(
        {"message": "Movie rated successfully and suggestions updated."},
        status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED

    )


@api_view(['POST'])
def add_community_comment(request):
    # Step 1: Validate input data
    user_id = request.data.get('user_id')
    movie_id = request.data.get('movie_id')
    content = request.data.get('content')

    # Step 2: Check if the user and movie exist
    try:
        user = User.objects.get(id=user_id)
        movie = Movie.objects.get(id=movie_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Movie.DoesNotExist:
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

    # Step 3: Check if the user has watched the movie
    if not UserWatchedMovie.objects.filter(user=user, movie=movie).exists():
        return Response({"error": "You must watch the movie before commenting."}, status=status.HTTP_403_FORBIDDEN)

    # Step 4: Create the comment
    try:
        comment = MovieCommunity.objects.create(
            movie=movie,
            user=user,
            content=content
        )
        return Response(
            {"message": "Comment added successfully.", "comment_id": comment.id},
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['DELETE'])
def delete_community_comment(request, comment_id):
    # Step 1: Get the user ID from the request
    user_id = request.query_params.get('user_id')

    # Step 2: Check if the user exists
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({comment_id}, status=status.HTTP_404_NOT_FOUND)

    # Step 3: Retrieve the comment
    try:
        comment = MovieCommunity.objects.get(id=comment_id)
    except MovieCommunity.DoesNotExist:
        return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)

    # Step 4: Ensure the user is the owner of the comment
    if comment.user != user:
        return Response({"error": "You are not authorized to delete this comment."}, status=status.HTTP_403_FORBIDDEN)

    # Step 5: Delete the comment
    comment.delete()
    return Response({"message": "Comment deleted successfully."}, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_movie_comments(request, movie_id):
    # Step 1: Extract user_id from the request
    user_id = request.query_params.get('user_id')

    # Step 2: Validate user_id
    if not user_id:
        return Response({"error": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    # Step 3: Check if the movie exists
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return Response({"error": "Movie not found."}, status=status.HTTP_404_NOT_FOUND)

    # Step 4: Verify that the user has watched the movie
    if not UserWatchedMovie.objects.filter(user=user, movie=movie).exists():
        return Response({"error": "You must watch the movie to view its comments."}, status=status.HTTP_403_FORBIDDEN)

    # Step 5: Retrieve all comments for the movie
    comments = MovieCommunity.objects.filter(movie=movie).order_by('-add_date') 

    # Step 6: Serialize the data
    serializer = MovieCommentSerializer(comments, many=True)

    # Step 7: Return the serialized data
    return Response(serializer.data, status=status.HTTP_200_OK)

# get rated movie API
@api_view(['GET'])
def get_watched_movie_ids(request, user_id):
    # Step 1: Check if the user exists
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    # Step 2: Retrieve all watched movie IDs for the user
    watched_movies = UserWatchedMovie.objects.filter(user=user).values_list('movie_id', flat=True)

    # Step 3: Convert the QuerySet to a list and return it
    return Response({"watched_movie_ids": list(watched_movies)}, status=status.HTTP_200_OK)



#### APIs to be proccessed ####

# create a group API
# join a group API
# block user from group API
# write a post API
# like a post API
# comment in a post API
# get group post API
# get user group post API
# leave a group
# delete a post

###############################



#### Useful Functions ####

def genres_delta(list1, list2):
    le = max(len(list1), len(list2))
    if le == 0:
        return 0
    qu = le * (le + 1) / 2
    tot = 1000 / qu
    val = 0
    for i in range(len(list1)):
        for j in range(len(list2)):
            if list1[i] == list2[j].genre_id:
                val += int(((le - max(i, j)) * tot) + 0.5)
    return val

def create_initial_movie_suggestions(user):
    # Get all movies
    movies = Movie.objects.all()

    # Create suggestions for each movie
    for movie in movies:
        suggestion = UserSuggestionList(
            user=user, movie=movie, total=0, is_watched=False
        )
        suggestion.save()

def update_suggestions(user_id, genre_ids):
    
    # read old genres and adjust points
    user_old_genres = UserGenre.objects.filter(user_id=user_id)
    user_suggestions = UserSuggestionList.objects.filter(user_id=user_id)

    for suggestion in user_suggestions:
        cur_suggestion = MovieGenre.objects.filter(movie_id=suggestion.movie_id)
        suggestion.total -= genres_delta(user_old_genres, cur_suggestion)
        suggestion.save()

    # clear old genres and add new ones
    UserGenre.objects.filter(user_id=user_id).delete()
    for genre_id in genre_ids:
        UserGenre.objects.create(user_id=user_id, genre_id=genre_id)

    # recalculate points based on new genres
    for suggestion in user_suggestions:
        cur_suggestion = MovieGenre.objects.filter(movie_id=suggestion.movie_id)
        suggestion.total = genres_delta(genre_ids, list(cur_suggestion))
        suggestion.save()

def update_suggestions_by_rate(user_id, movie_id, rating, subtract=False):
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
        point = points_list[i]  # Get the corresponding point from the file
        suggestion, _ = UserSuggestionList.objects.get_or_create(
            user_id=user_id,
            movie_id=related_movie.related_id,  # Use the related movie ID
            defaults={"total": 0, "is_watched": False}
        )

        # Add or subtract the point based on the `subtract` flag
        if subtract:
            suggestion.total -= point
        else:
            suggestion.total += point

        suggestion.save()