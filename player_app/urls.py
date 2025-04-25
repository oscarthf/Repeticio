
from django.urls import path
from player_app import views

urlpatterns = [
    path('', views.home, name='home'),
    path('player', views.player, name='player'),
]
