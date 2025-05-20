from django.db import models
from APIs.models.movie_model import Movie
from APIs.models.director_model import Director

class MovieDirector(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    director = models.ForeignKey(Director, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("movie", "director")