import tweepy
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.shortcuts import HttpResponse, get_object_or_404, redirect, render
from dateutil import parser
from home.models import Log, Schedule
from home.views import twitter_api, schedule_tweet
from datetime import datetime
from .models import Colaboration

# Create your views here.

CONSUMER_KEY = settings.CONSUMER_KEY
CONSUMER_SECRET = settings.CONSUMER_SECRET


@login_required(login_url="home-page")
def request(request):
    colabTable = Colaboration.objects.filter(COlabUserName=request.user.username)
    context = {
        "page": "colab",
        "data": colabTable
    }
    return render(request, 'colaborate/RequestPage.html', context)

@login_required(login_url="home-page")
def send(request):
    if request.method == "POST":
        username = request.POST.get('username')
        user = User.objects.filter(username=username)
        if user.count() >= 1:
            colabData = Colaboration.objects.filter(ColabMe=request.user, COlabUserName=username)
            if colabData.count() >=1:
                messages.warning(request, "Request Already Sent.")
            else:
                colab = Colaboration.objects.create(ColabMe=request.user, COlabUserName=username)
                colab.save()
                log = Log.objects.create(
                    user=request.user, action="Invitation Send To user @{}".format(username))
                log.save()
                messages.success(request, "Request Send Success.")
        else:
            messages.warning(request, "User Not Exist!")
    colabTable = Colaboration.objects.filter(ColabMe=request.user)
    context = {
        "page": "colab",
        "data": colabTable
    }
    return render(request, 'colaborate/SendPage.html', context)

@login_required(login_url="home-page")
def accept(request, id):
    colabData = get_object_or_404(Colaboration, id=id)
    if colabData.COlabUserName == request.user.username:
        log = Log.objects.create(
            user=request.user, action="Connection Created With user @{}".format(colabData.ColabMe.username))
        log.save()
        red = True
        colabData.Status = True
        colabData.save()
    messages.success(request, "successfully Accepted")
    return redirect('colab-request')


@login_required(login_url="home-page")
def remove(request, id):
    colabData = get_object_or_404(Colaboration, id=id)
    log = Log.objects.create(
        user=request.user, action="Connection Removed With user @{}".format(colabData.ColabMe.username))
    log.save()
    red = True
    colabData.delete()
    messages.success(request, "successfully removed")
    if red:
        return redirect('colab-request')
    else:
        return redirect('colab-send')


@login_required(login_url="home-page")
def work(request, id):
    get_object_or_404(Colaboration, id=id)
    context = {
        "page": "colab",
        "id": id
    }
    return render(request, 'colaborate/home.html', context)


# def twitter_api(user):
#     auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
#     userObj = User.objects.get(username=user.username)
#     tokens = userObj.accesstoken_set.get()
#     auth.set_access_token(tokens.access_token, tokens.access_token_secrete)
#     api = tweepy.API(auth)
#     return api



@login_required(login_url="home-page")
def tweet(request, id):
    if request.method == "POST":
        colabData = get_object_or_404(Colaboration, id=id)
        api = twitter_api(colabData.ColabMe)
        status = request.POST.get('tweet')
        if 'file' in request.FILES:
            a = request.FILES['file'].name
            if a.endswith(".png") or a.endswith(".jpeg") or a.endswith(".jpg"):
                fs = FileSystemStorage()
                fileobj = fs.save(a, request.FILES['file'])
                api.update_with_media(fs.path(fileobj), status)
                log = Log.objects.create(
                    user=request.user, action="Tweet With Image by user@{}".format(request.user.username))
                log.save()
                fs.delete(fileobj)
                messages.success(request, 'Successfully tweeted')
            else:
                messages.warning(request, "Must Be a Image File")
        else:
            api.update_status(status)
            messages.success(request, 'Successfully tweeted')
            log = Log.objects.create(user=request.user, action="Text Tweet by user @{}".format(request.user.username))
            log.save()
    context = {
        "page": "colab",
    }
    return render(request, 'colaborate/tweet.html', context)


@login_required(login_url="home-page")
def schedule(request, id):
    context = {
        'schedule': True,
        "page": "colab",
    }
    if request.method == "POST":
        colabData = get_object_or_404(Colaboration, id=id)
        userTime = parser.parse(str(request.POST.get(
            "sc-date"))+" "+str(request.POST.get("sc-time")))
        currTime = datetime.now().replace(second=0, microsecond=0)
        if userTime <= currTime:
            messages.warning(request, "You Selected Previous Time")
            return redirect("colab-schedule")
        else:
            diffTime = userTime - datetime.now()
            diffSecond = diffTime.seconds

            status = request.POST.get('tweet')
            if 'file' in request.FILES:
                a = request.FILES['file'].name
                if a.endswith(".png") or a.endswith(".jpeg") or a.endswith(".jpg"):
                    sch = Schedule.objects.create(
                        user=colabData.ColabMe, tweet=status, twFile=request.FILES['file']
                    )
                    sch.save()
                    schedule_tweet(sch.id, request.user.username, schedule=diffSecond, priority=5)
                    log = Log.objects.create(user=request.user, action="Tweet Scheduled To Run On {} With Media by user @{}".format(
                        str(request.POST.get("sc-date"))+" "+str(request.POST.get("sc-time")), request.user.username))
                    log.save()
                    messages.success(
                        request, 'Successfully Scheduled for {} {}'.format(request.POST.get("sc-date"), request.POST.get("sc-time")))
                else:
                    messages.warning(request, "Must Be a Image File")
            else:
                sch = Schedule.objects.create(
                    user=colabData.ColabMe, tweet=status
                )
                sch.save()
                schedule_tweet(sch.id, request.user.username, schedule=diffSecond, priority=5)
                log = Log.objects.create(user=request.user, action="Tweet Scheduled To Run On {} With Text by user @{}".format(
                    str(request.POST.get("sc-date"))+" "+str(request.POST.get("sc-time")), request.user.username))
                log.save()
                messages.success(
                    request, 'Successfully Scheduled for {} {}'.format(request.POST.get("sc-date"), request.POST.get("sc-time")))
    return render(request, 'colaborate/schedule.html', context)
