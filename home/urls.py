from django.urls import  path
from . import views as view
from django.conf import  settings
from django.conf.urls.static import static

urlpatterns = [
    path('', view.index, name='home-page'),
    path('dashboard/', view.home, name='home-dash'),
    path('callback/', view.callback, name='callback'),
    path('logout/', view.logout_request, name='logout'),
    path('tweet/', view.tweet, name='home-tweet'),
    path('schedule/', view.schedule, name='home-schedule'),
    path('sentiment/', view.do_sentiment, name='home-sentiment'),
    path('sentimental_redirect/', view.sentimental_redirect, name='sent-redirect'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

