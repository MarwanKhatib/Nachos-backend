from django.db import models
from APIs.models.movie_model import Movie
from APIs.models.writer_model import Writer

class MovieWriter(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    writer = models.ForeignKey(Writer, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("movie", "writer")