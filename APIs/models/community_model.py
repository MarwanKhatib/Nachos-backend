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

class UserSuggestionList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    total = models.IntegerField()
    is_watched = models.BooleanField(default=False)