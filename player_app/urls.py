
from django.urls import include, path
from django.contrib.auth import views as auth_views

from player_app import views

urlpatterns = [
    
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('social-auth/', include('social_django.urls', namespace='social')),

    path('', views.home, name='home'),
    path('settings', views.app_settings, name='settings'),

    path('select_learning_language', views.select_learning_language, name='select_learning_language'),
    path('select_ui_language', views.select_ui_language, name='select_ui_language'),
    path('set_learning_language', views.set_learning_language, name='set_learning_language'),
    path('set_ui_language', views.set_ui_language, name='set_ui_language'),

    path('create_new_exercise', views.create_new_exercise, name='create_new_exercise'),
    path('get_created_exercise', views.get_created_exercise, name='get_created_exercise'),
    path('submit_answer', views.submit_answer, name='submit_answer'),
    path('apply_thumbs_up_or_down', views.apply_thumbs_up_or_down, name='apply_thumbs_up_or_down'),

    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('customer-portal/', views.customer_portal, name='customer_portal'),
]
