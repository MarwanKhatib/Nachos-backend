"""User model module for handling user authentication and profile management.

This module defines the custom User model that extends Django's AbstractUser,
adding additional functionality for user profiles and email verification.
"""

import random

from django.contrib.auth.models import AbstractUser
from django.db import models

from ..managers import CustomUserManager


class User(AbstractUser):
    """Custom user model extending Django's AbstractUser.

    This model adds additional fields for user profile management including:
    - Birth date
    - Watch count tracking
    - Join date
    - Email verification functionality

    Uses email as the primary identifier for authentication instead of username.
    """

    # Add new fields
    birth_date = models.DateField(null=True, blank=True)
    watched_no = models.IntegerField(default=0)
    join_date = models.DateField(auto_now_add=True)

    # Email verification fields
    auth_key = models.CharField(max_length=6, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    # Override username field to make it unique
    username = models.CharField(
        max_length=50,
        unique=True,
        error_messages={
            "unique": "A user with that username already exists.",
        },
    )

    # Override email field to make it unique
    email = models.EmailField(
        unique=True,
        error_messages={
            "unique": "A user with that email already exists.",
        },
    )

    # Override first_name and last_name to allow null and blank
    first_name = models.CharField(max_length=150, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)

    # Use email as the username field for authentication

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = CustomUserManager()

    def __str__(self) -> str:
        """Return the string representation of the user."""
        return str(self.username)

    def generate_auth_key(self):
        """Generate a new 6-digit auth key"""
        self.auth_key = "".join(random.choices("0123456789", k=6))
        self.save()
        return self.auth_key

    def verify_email(self, provided_key):
        """Verify email with provided key"""
        if not self.auth_key:
            return False

        if self.auth_key == provided_key:
            self.is_email_verified = True
            self.is_active = True
            self.auth_key = None  # Clear the auth key after successful verification
            self.save()
            return True
        return False
