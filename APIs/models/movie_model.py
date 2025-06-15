from django.db import models
from APIs.models.language_model import Language

class Movie(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    trailer = models.TextField()
    poster = models.TextField()
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name
