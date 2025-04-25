
from django.urls import include, path
from django.contrib.auth import views as auth_views

from player_app import views

urlpatterns = [
    
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('social-auth/', include('social_django.urls', namespace='social')),

    path('', views.player, name='player'),
    path('settings', views.settings, name='settings'),
]
