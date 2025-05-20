from django.db import models
from APIs.models.movie_model import Movie

class RelatedMovie(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="related_movie_main")
    related = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="related_movie_related")
    priority = models.IntegerField()

    class Meta:
        unique_together = ("movie", "related")