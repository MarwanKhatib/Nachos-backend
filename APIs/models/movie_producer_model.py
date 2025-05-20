from django.db import models
from APIs.models.movie_model import Movie
from APIs.models.producer_model import Producer

class MovieProducer(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    producer = models.ForeignKey(Producer, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("movie", "producer")