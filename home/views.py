from django.shortcuts import render, redirect
from django.http import HttpResponse
import tweepy
from decouple import config
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth.models import User
from .models import AccessToken, Schedule
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from dateutil import parser
from datetime import datetime
from background_task import background
from django.conf import settings
CONSUMER_KEY = settings.CONSUMER_KEY
CONSUMER_SECRET = settings.CONSUMER_SECRET

# Create your views here.
@background
def schedule_tweet(tweetid):
    getTweet = Schedule.objects.get(id=tweetid)
    api = twitter_api(getTweet.user)
    status = getTweet.tweet
    if bool(getTweet.twFile):
        fileName = str(settings.BASE_DIR)+'/'+str(getTweet.twFile.name)
        api.update_with_media(fileName, status)
    else:
        api.update_status(status)


def twitter_api(user):
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    userObj = User.objects.get(username=user.username)
    tokens = userObj.accesstoken_set.get()
    auth.set_access_token(tokens.access_token, tokens.access_token_secrete)
    api = tweepy.API(auth)
    return api


def index(request):
    if request.user.is_authenticated:
        context = {
            'auth': True
        }
    else:
        if 'request_token' in request.session and 'redirect_url' in request.session:
            context = {
                'url': request.session['redirect_url'],
                'auth': False
            }
        else:
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
    # getTweet = Schedule.objects.get(user=request.user)
    print(settings.BASE_DIR)

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
        messages.success(request, 'Successfully SignedIn')
        return redirect('home-dash')
    else:
        user_obj = User.objects.create_user(username=me.screen_name)
        user_obj.save()
        access_model = AccessToken.objects.create(
            user=user_obj, access_token=access_token, access_token_secrete=access_token_secret)
        access_model.save()
        login(request, user_obj)
        messages.success(request, 'Successfully SignedUp')
        return redirect('home-dash')
    return HttpResponse('Something is wrong')


def tweet(request):
    if request.method == "POST":
        api = twitter_api(request.user)
        status = request.POST.get('tweet')
        if 'file' in request.FILES:
            a = request.FILES['file'].name
            if a.endswith(".png") or a.endswith(".jpeg") or a.endswith(".jpg"):
                fs = FileSystemStorage()
                fileobj = fs.save(a, request.FILES['file'])
                api.update_with_media(fs.path(fileobj), status)
                fs.delete(fileobj)
                messages.success(request, 'Successfully tweeted')
            else:
                messages.warning(request, "Must Be a Image File")
        else:
            api.update_status(status)
    return render(request, 'home/tweet.html')


def schedule(request):
    context = {
        'schedule': True
    }
    if request.method == "POST":
        userTime = parser.parse(str(request.POST.get(
            "sc-date"))+" "+str(request.POST.get("sc-time")))
        currTime = datetime.now().replace(second=0, microsecond=0)
        if userTime <= currTime:
            messages.warning(request, "You Selected Previous Time")
            return redirect("home-schedule")
        else:
            diffTime = userTime - datetime.now()
            diffSecond = diffTime.seconds

            status = request.POST.get('tweet')
            if 'file' in request.FILES:
                a = request.FILES['file'].name
                if a.endswith(".png") or a.endswith(".jpeg") or a.endswith(".jpg"):
                    sch = Schedule.objects.create(
                        user=request.user, tweet=status, twFile=request.FILES['file']
                    )
                    sch.save()
                    schedule_tweet(sch.id, schedule=diffSecond)
                    messages.success(
                        request, 'Successfully Scheduled for <b>{}</b>'.format(request.POST.get("sc-date")))
                else:
                    messages.warning(request, "Must Be a Image File")
            else:
                sch = Schedule.objects.create(
                    user=request.user, tweet=status
                )
                sch.save()
                schedule_tweet(sch.id, schedule=diffSecond)
                messages.success(
                    request, 'Successfully Scheduled for <b>{}</b>'.format(request.POST.get("sc-date")))
    return render(request, 'home/schedule.html', context)


def logout_request(request):
    logout(request)
    return redirect('home-page')
