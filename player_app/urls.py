
from django.urls import path

from player_app import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('player', views.player, name='player'),
]
