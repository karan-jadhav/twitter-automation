from django.urls import path
from . import views as view

urlpatterns = [
    path('', view.request, name="colab-request"),
    path('send/', view.send, name="colab-send"),
    path('accept/<int:id>/', view.accept, name="colab-accept"),
    path('remove/<int:id>/', view.remove, name="colab-remove"),
    path('work/<int:id>/', view.work, name="colab-work"),
    path('work/<int:id>/tweet/', view.tweet, name="colab-tweet"),
    path('work/<int:id>/schedule/', view.schedule, name="colab-schedule"),
]
