
from django.urls import include, path
from django.contrib.auth import views as auth_views

from player_app import views

urlpatterns = [
    
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('social-auth/', include('social_django.urls', namespace='social')),

    path('', views.home, name='home'),
    path('settings', views.settings, name='settings'),

    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('customer-portal/', views.customer_portal, name='customer_portal'),
]
