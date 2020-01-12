from django.urls import  path
from . import views as view
urlpatterns = [
    path('', view.index, name='home-page'),
    path('callback/', view.callback, name='callback'),
]