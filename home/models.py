from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class AccessToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=200)
    access_token_secrete = models.CharField(max_length=200)


class Schedule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tweet = models.TextField()
    twFile = models.FileField(blank=True, null=True)
