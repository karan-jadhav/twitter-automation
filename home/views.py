from django.shortcuts import render
from django.http import  HttpResponse
import tweepy

# Create your views here.

def index(request):
    return render(request, 'home/index.html')

def callback(request):
    return HttpResponse('200 ok')