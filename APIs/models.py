import random

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import CustomUserManager

# class User(AbstractBaseUser):

#     email = models.EmailField(unique=True)
#     username = models.CharField(unique=True, max_length=50)
#     birth_date = models.DateField(null=True, blank=True)
#     watched_no = models.IntegerField(default=0)
#     join_date = models.DateField(auto_now_add=True)
#     is_active = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=False)

#     # Email verification fields
#     auth_key = models.CharField(
#         max_length=6, blank=True, null=True
#     )  # Store the 6-digit key
#     is_email_verified = models.BooleanField(
#         default=False
#     )  # Track email verification status

#     USERNAME_FIELD = "username"  # login identifier
#     REQUIRED_FIELDS = ["email"]

#     objects = CustomUserManager()  # Link to the custom manager

#     def __str__(self):
#         return self.username

#     def generate_auth_key(self):
#         self.auth_key = "".join(random.choices("0123456789", k=6))
#         self.save()

#     def verify_email(self, provided_key):
#         if self.auth_key == provided_key:
#             self.is_email_verified = True
#             self.auth_key = None
#             self.save()
#             return True
#         return False


class User(AbstractBaseUser, PermissionsMixin):  # add PermissionsMixin here

    email = models.EmailField(unique=True)
    username = models.CharField(unique=True, max_length=50)
    birth_date = models.DateField(null=True, blank=True)
    watched_no = models.IntegerField(default=0)
    join_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # Email verification fields
    auth_key = models.CharField(max_length=6, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = CustomUserManager()

    def __str__(self):
        return self.username

    def generate_auth_key(self):
        self.auth_key = "".join(random.choices("0123456789", k=6))
        self.save()

    def verify_email(self, provided_key):
        if self.auth_key == provided_key:
            self.is_email_verified = True
            self.auth_key = None
            self.save()
            return True
        return False


### read only data ###


class Genre(models.Model):
    name = models.CharField(max_length=30)


class Language(models.Model):
    name = models.CharField(max_length=5)


class Actor(models.Model):
    name = models.CharField(max_length=50)


class Director(models.Model):
    name = models.CharField(max_length=50)


class Writer(models.Model):
    name = models.CharField(max_length=50)


class Producer(models.Model):
    name = models.CharField(max_length=50)


class Movie(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    trailer = models.TextField()
    poster = models.TextField()
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True)


class RelatedMovie(models.Model):
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name="related_movie_main"
    )
    related = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name="related_movie_related"
    )
    priority = models.IntegerField()


class MovieActor(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)


class MovieDirector(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    director = models.ForeignKey(Director, on_delete=models.CASCADE)


class MovieWriter(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    writer = models.ForeignKey(Writer, on_delete=models.CASCADE)


class MovieProducer(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    producer = models.ForeignKey(Producer, on_delete=models.CASCADE)


class MovieGenre(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)


### end of read only data ###


class UserGenre(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_genres")
    genre = models.ForeignKey(
        Genre, on_delete=models.CASCADE, related_name="genre_users"
    )

    class Meta:
        unique_together = ("user", "genre")


class MovieCommunity(
    models.Model
):  # Represents the comment in the movie comment section
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.CharField(max_length=255)


class UserWatchedMovie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rate = models.FloatField()
    watch_date = models.DateTimeField(auto_now_add=True)


class UserWatchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    add_date = models.DateTimeField(auto_now_add=True)


class UserSuggestionList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    total = (
        models.IntegerField()
    )  # the higher it is the more likely it is to be suggested
    is_watched = models.BooleanField(default=False)


class Group(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    create_date = models.DateField(auto_now_add=True)


class UserGroup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)


class Post(models.Model):
    content = models.CharField(max_length=255)
    add_date = models.DateTimeField(auto_now_add=True)
    reaction_no = models.IntegerField(default=0)
    comment_no = models.IntegerField(default=0)


class UserPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)


class UserReact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)


class UserComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    content = models.CharField(max_length=255)
    add_date = models.DateTimeField(auto_now_add=True)
