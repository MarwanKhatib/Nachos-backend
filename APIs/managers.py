import random
from datetime import timedelta

import yagmail
from decouple import config
from django.contrib.auth.base_user import BaseUserManager
from django.utils.timezone import now


class CustomUserManager(BaseUserManager):

    def create_user(
        self, email, username, password=None, birth_date=None, **extra_fields
    ):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(
            email=email, username=username, birth_date=birth_date, **extra_fields
        )
        user.set_password(password)  # Hash the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, username, password, **extra_fields)

    def register_user(self, email, username, password, birth_date):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)

        # Validate birth_date age >= 16
        min_birth_date = now().date() - timedelta(days=16 * 365)
        if birth_date > min_birth_date:
            raise ValueError("You must be at least 16 years old to register.")

        # Creating user
        user = self.create_user(
            email=email,
            username=username,
            password=password,
            birth_date=birth_date,
            is_active=False,
        )

        # Generate a 6-digit verification key
        auth_key = "".join(random.choices("0123456789", k=6))
        user.auth_key = auth_key
        user.save()

        # Send the verification email
        yag = yagmail.SMTP(config("EMAIL_HOST_USER"), config("EMAIL_HOST_PASSWORD"))

        yag.send(
            to=email,
            subject="Verify Your Email",
            contents=f"Your verification code is: {auth_key}",
        )

        return user

