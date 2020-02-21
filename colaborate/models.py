from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Colaboration(models.Model):
    ColabMe = models.ForeignKey(User, on_delete=models.CASCADE)
    COlabUserName = models.CharField(max_length=200)
    