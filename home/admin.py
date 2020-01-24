from django.contrib import admin
from .models import  AccessToken, Schedule, Log
# Register your models here.

admin.site.register(AccessToken)
admin.site.register(Schedule)
admin.site.register(Log)