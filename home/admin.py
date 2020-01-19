from django.contrib import admin
from .models import  AccessToken, Schedule
# Register your models here.

admin.site.register(AccessToken)
admin.site.register(Schedule)