from django.db import models
from APIs.models.movie_model import Movie
from APIs.models.actor_model import Actor

class MovieActor(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("movie", "actor")