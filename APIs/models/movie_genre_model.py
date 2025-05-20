from django.db import models
from APIs.models.movie_model import Movie
from APIs.models.genre_model import Genre

class MovieGenre(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("movie", "genre")