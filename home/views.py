from django.shortcuts import render, redirect
from django.http import  HttpResponse
import tweepy
from decouple import config
from django.contrib.auth import  logout, login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth.models import User
from .models import  AccessToken
CONSUMER_KEY = settings.CONSUMER_KEY
CONSUMER_SECRET = settings.CONSUMER_SECRET

# Create your views here.

def index(request):
    if request.user.is_authenticated:
        context = {
            'auth':True
        }    
    else:
        if 'request_token' in request.session and 'redirect_url' in request.session:
            print('already  generated')
            context = {
                'url': request.session['redirect_url'], 
                'auth': False
            }
        else:
            print('new generated')
            auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
            redirect_url = auth.get_authorization_url()
            request.session['redirect_url'] = redirect_url
            request.session['request_token'] = auth.request_token
            context = {
                'url': redirect_url, 
                'auth': False
            }
    return render(request, 'home/index.html', context)
@login_required(login_url='home-page')
def home(request):
    return render(request, 'home/home.html')

def callback(request):
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    token = request.session.get('request_token')
    del request.session['request_token']
    del request.session['redirect_url']
    auth.request_token = token
    verifier = request.GET.get('oauth_verifier')
    access_token, access_token_secret = auth.get_access_token(verifier)
    api = tweepy.API(auth)
    me = api.me()
    if User.objects.filter(username=me.screen_name).count() > 0:
        user = User.objects.get(username=me.screen_name)
        login(request, user)
        return redirect('home-dash')
    else:
        user_obj = User.objects.create_user(username=me.screen_name)
        user_obj.save()
        access_model = AccessToken.objects.create(user=user_obj, access_token=access_token, access_token_secrete=access_token_secret)
        access_model.save()
        return redirect('home-dash')
    return HttpResponse('Something is wrong')

def logout_request(request):
    logout(request)
    return redirect('home-page')