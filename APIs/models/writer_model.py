"""
This module defines the Writer model for the Nachos backend.
The Writer model represents authors/writers in the system and their basic information.
"""

from django.db import models


class Writer(models.Model):
    """
    Model representing a writer/author in the system.

    This model stores basic information about writers including their names.
    """

    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return str(self.name)
