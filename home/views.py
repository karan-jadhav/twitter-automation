from django.shortcuts import render, redirect
from django.http import HttpResponse
import tweepy
from decouple import config
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth.models import User
from .models import AccessToken, Schedule, Log
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from dateutil import parser
from datetime import datetime
from background_task import background
import re
from textblob import TextBlob
from io import BytesIO
import base64
import matplotlib.pyplot as plt


CONSUMER_KEY = settings.CONSUMER_KEY
CONSUMER_SECRET = settings.CONSUMER_SECRET

# Create your views here.
@background
def schedule_tweet(tweetid, colab):
    getTweet = Schedule.objects.get(id=tweetid)
    api = twitter_api(getTweet.user)
    status = getTweet.tweet
    if bool(getTweet.twFile):
        fileName = str(settings.BASE_DIR)+'/media/'+str(getTweet.twFile.name)
        api.update_with_media(fileName, status)
        if colab:
            log = Log.objects.create(
                user=getTweet.user, action="Scheduled Tweet With Image by user @{}".format(colab))
            log.save()
        else:
            log = Log.objects.create(
                user=getTweet.user, action="Scheduled Tweet With Image")
            log.save()
    else:
        api.update_status(status)
        if colab:
            log = Log.objects.create(
                user=getTweet.user, action="Scheduled Text Tweet by user @{}".format(colab))
            log.save()
        else:
            log = Log.objects.create(
                user=getTweet.user, action="Scheduled Text Tweet")
            log.save()


def get_plot(user):
    polarity = 0
    positive = 0
    wpositive = 0
    spositive = 0
    negative = 0
    wnegative = 0
    snegative = 0
    neutral = 0
    table = {}
    api = twitter_api(user)
    mentions = api.mentions_timeline()
    NoOfMentions = len(mentions)
    itrCount = 0
    for mention in mentions:
        text = ' '.join(re.sub(
            "(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) | (\w +:\ / \ / \S +)", " ", mention.text).split())
        analysis = TextBlob(text)
        polarity += analysis.sentiment.polarity
        table[itrCount] = {"tweet":text, "screenname":mention.user.screen_name}
        if (analysis.sentiment.polarity == 0):
            neutral += 1
            table[itrCount]['polarity'] = "Neutral"
        elif (analysis.sentiment.polarity > 0 and analysis.sentiment.polarity <= 0.3):
            wpositive += 1
            table[itrCount]['polarity'] = "Weakly Positive"
        elif (analysis.sentiment.polarity > 0.3 and analysis.sentiment.polarity <= 0.6):
            positive += 1
            table[itrCount]['polarity'] = "Positive"
        elif (analysis.sentiment.polarity > 0.6 and analysis.sentiment.polarity <= 1):
            spositive += 1
            table[itrCount]['polarity'] = "Strongly Positive"
        elif (analysis.sentiment.polarity > -0.3 and analysis.sentiment.polarity <= 0):
            wnegative += 1
            table[itrCount]['polarity']="Weakly negative"
        elif (analysis.sentiment.polarity > -0.6 and analysis.sentiment.polarity <= -0.3):
            negative += 1
            table[itrCount]['polarity'] = "Negative"
        elif (analysis.sentiment.polarity > -1 and analysis.sentiment.polarity <= -0.6):
            snegative += 1
            table[itrCount]['polarity'] = "Strongly Negative"
        itrCount+=1

    positive = format(100 * float(positive) / float(NoOfMentions), '.2f')
    wpositive = format(100 * float(wpositive) / float(NoOfMentions), '.2f')
    spositive = format(100 * float(spositive) / float(NoOfMentions), '.2f')
    negative = format(100 * float(negative) / float(NoOfMentions), '.2f')
    wnegative = format(100 * float(wnegative) / float(NoOfMentions), '.2f')
    snegative = format(100 * float(snegative) / float(NoOfMentions), '.2f')
    neutral = format(100 * float(neutral) / float(NoOfMentions), '.2f')
    polarity = polarity / NoOfMentions
    labels = ['Positive [' + str(positive) + '%]', 'Weakly Positive [' + str(wpositive) + '%]', 'Strongly Positive [' + str(spositive) + '%]', 'Neutral [' + str(
        neutral) + '%]', 'Negative [' + str(negative) + '%]', 'Weakly Negative [' + str(wnegative) + '%]', 'Strongly Negative [' + str(snegative) + '%]']
    sizes = [positive, wpositive, spositive,
             neutral, negative, wnegative, snegative]
    colors = ['yellowgreen', 'lightgreen', 'darkgreen',
              'gold', 'red', 'lightsalmon', 'darkred']

    patches, texts = plt.pie(sizes, colors=colors, startangle=90)
    plt.legend(patches, labels, loc="best")
    plt.title('Sentimental Analysis of {} Tweets'.format(NoOfMentions))
    plt.axis('equal')
    plt.tight_layout()
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')
    return graphic, table


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
            'auth': True,
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
                'auth': False,
            }
    context['page'] = 'home'
    return render(request, 'home/index.html', context)


@login_required(login_url='home-page')
def home(request):
    context = {
        'page': 'dash'
    }
    return render(request, 'home/home.html', context)


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

@login_required(login_url="home-page")
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
                log = Log.objects.create(
                    user=request.user, action="Tweet With Image")
                log.save()
                fs.delete(fileobj)
                messages.success(request, 'Successfully tweeted')
            else:
                messages.warning(request, "Must Be a Image File")
        else:
            api.update_status(status)
            messages.success(request, 'Successfully tweeted')
            log = Log.objects.create(user=request.user, action="Text Tweet")
            log.save()
    context = {
        'page': 'dash'
    }
    return render(request, 'home/tweet.html', context)

@login_required(login_url="home-page")
def schedule(request):
    context = {
        'schedule': True,
        'page': 'dash'
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
                    schedule_tweet(sch.id, False, schedule=diffSecond, priority=5)
                    log = Log.objects.create(user=request.user, action="Tweet Scheduled To Run On {} With Media".format(
                        str(request.POST.get("sc-date"))+" "+str(request.POST.get("sc-time"))))
                    log.save()
                    messages.success(
                        request, 'Successfully Scheduled for {} {}'.format(request.POST.get("sc-date"), request.POST.get("sc-time")))
                else:
                    messages.warning(request, "Must Be a Image File")
            else:
                sch = Schedule.objects.create(
                    user=request.user, tweet=status
                )
                sch.save()
                schedule_tweet(sch.id, False, schedule=diffSecond, priority=5)
                log = Log.objects.create(user=request.user, action="Tweet Scheduled To Run On {} With Text".format(
                    str(request.POST.get("sc-date"))+" "+str(request.POST.get("sc-time"))))
                log.save()
                messages.success(
                    request, 'Successfully Scheduled for {} {}'.format(request.POST.get("sc-date"), request.POST.get("sc-time")))
    return render(request, 'home/schedule.html', context)

@login_required(login_url="home-page")
def do_sentiment(request):
    Plot, table = get_plot(request.user)
    context = {
        'sentiment': True,
        'graphic': Plot,
        'table': table,
        'page': 'dash'
    }
    return render(request, 'home/sentiment.html', context)

@login_required(login_url="home-page")
def sentimental_redirect(request):
    context = {
        'analyze': True,
        'page': 'dash'
    }
    return render(request, 'home/sentiment_redirect.html', context)

@login_required(login_url="home-page")
def show_logs(request):
    all_logs = Log.objects.filter(user=request.user)
    context = {
        'logs': all_logs,
        'page': 'dash'
    }
    return render(request, 'home/logs.html', context)
    
@login_required(login_url="home-page")
def logout_request(request):
    logout(request)
    return redirect('home-page')
