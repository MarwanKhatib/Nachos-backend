from django.db import models
from APIs.models.user_model import User

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