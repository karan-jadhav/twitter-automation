from django.shortcuts import render
import tweepy

# Create your views here.

def index(request):
    return render(request, 'home/index.html')