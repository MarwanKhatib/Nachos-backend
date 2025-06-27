from django.db import models
from APIs.models.user_model import User
from APIs.models.movie_model import Movie
from APIs.models.genre_model import Genre

class UserGenre(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_genres")
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, related_name="genre_users")

    class Meta:
        unique_together = ("user", "genre")

class MovieCommunity(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.CharField(max_length=255)
    add_date = models.DateTimeField(auto_now_add=True)

class UserWatchedMovie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rate = models.FloatField()
    watch_date = models.DateTimeField(auto_now_add=True)

class UserWatchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    add_date = models.DateTimeField(auto_now_add=True)

# New intermediary model for UserMovieSuggestion
class UserMovieSuggestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="movie_suggestions")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="user_suggestions")
    total = models.IntegerField(default=0) # This will store the calculated suggestion score
    is_watched = models.BooleanField(default=False) # To track if the user has watched this suggested movie

    class Meta:
        unique_together = ("user", "movie")

# Modify UserSuggestionList to use the new intermediary model
class UserSuggestionList(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="suggestion_list_header")
    # The actual suggestions are now managed through UserMovieSuggestion
    # We can keep this model as a header or remove it if not strictly necessary
    # For now, I'll keep it as a header, but the core logic will use UserMovieSuggestion
    created_at = models.DateTimeField(auto_now_add=True)
