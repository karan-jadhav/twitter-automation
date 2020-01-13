from django.urls import  path
from . import views as view
urlpatterns = [
    path('', view.index, name='home-page'),
    path('dashboard/', view.home, name='home-dash'),
    path('callback/', view.callback, name='callback'),
    path('logout/', view.logout_request, name='logout')
]