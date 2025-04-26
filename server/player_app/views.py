
import datetime

import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

from django_ratelimit.decorators import ratelimit

from language_app_backend.util.db import get_global_container

from language_app_backend.util.constants import (CHECK_SUBSCRIPTION_INTERVAL, 
                                                 DEFAULT_RATELIMIT)

stripe.api_key = settings.STRIPE_SECRET_KEY

def check_subscription_active(user_id) -> bool:

    # Find Stripe customer by email
    customers = stripe.Customer.list(email=user_id).data
    if not customers:
        return False  # No customer found
    
    customer = customers[0]

    customer_id = customer.id

    subscriptions = stripe.Subscription.list(customer=customer_id, status='all')

    for sub in subscriptions.auto_paging_iter():
        if sub.status in ['active', 'trialing']:
            return True  # They have an active subscription
    return False  # No active subscription

def check_subscription_pipeline(global_container, user_id) -> bool:

    current_time = datetime.datetime.now(datetime.timezone.utc)
    
    check_subscription_interval = datetime.timedelta(seconds=CHECK_SUBSCRIPTION_INTERVAL)

    last_time_checked_subscription = global_container.get_last_time_checked_subscription(user_id)
    if last_time_checked_subscription is None:
        last_time_checked_subscription = current_time - 2 * check_subscription_interval
    
    if (current_time - last_time_checked_subscription) > check_subscription_interval:
        subscription_active = check_subscription_active(user_id)
        global_container.set_user_subscription(user_id, subscription_active)
        global_container.set_last_time_checked_subscription(user_id, current_time)
    else:
        subscription_active = global_container.get_user_subscription(user_id)

    return subscription_active
    
@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # or your desired post-login view
    return render(request, 'login.html')

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def create_checkout_session(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.email
    if len(settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)

    # Create Stripe checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='subscription',
        line_items=[{
            'price': settings.STRIPE_PRICE_ID,  # We'll set this in a minute
            'quantity': 1,
        }],
        success_url=f'{settings.FRONTEND_URL}/player/settings?session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url=f'{settings.FRONTEND_URL}/player/settings',
        customer_email=request.user.email,  # Important: use user's email from Google login
    )
    return redirect(session.url, code=303)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    global_container = get_global_container()

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_email')

        global_container.set_user_subscription(customer_email, True)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription['customer']

        # Find email by customer ID
        customer = stripe.Customer.retrieve(customer_id)
        customer_email = customer.email

        if customer_email:
            global_container.set_user_subscription(customer_email, False)

    return HttpResponse(status=200)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def customer_portal(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # First find the customer (you could save customer_id after checkout, or fetch by email)
    customers = stripe.Customer.list(email=request.user.email).data
    if not customers:
        return redirect('settings')  # fallback if no customer found
    customer = customers[0]

    session = stripe.billing_portal.Session.create(
        customer=customer.id,
        return_url=f'{settings.FRONTEND_URL}/player/settings',
    )
    return redirect(session.url)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def settings(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.email
    if len(settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    # check if language is set
    data = request.GET
    if not data:
        return redirect('select_language')
    language = data.get("language")
    if not language:
        return redirect('select_language')
    
    global_container = get_global_container()

    ######################

    is_subscribed = check_subscription_pipeline(global_container, user_id)

    if not is_subscribed:
        return redirect('create_checkout_session')

    ######################

    return render(request, "settings.html")

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.email
    if len(settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    # check if language is set
    data = request.GET
    if not data:
        return redirect('select_language')
    language = data.get("language")
    if not language:
        return redirect('select_language')
    
    global_container = get_global_container()
    
    ######################

    success = global_container.create_user_if_needed(user_id,
                                                     language)
    
    if not success:
        return redirect('select_language')
    
    ######################

    is_subscribed = check_subscription_pipeline(global_container, user_id)

    if not is_subscribed:
        return redirect('create_checkout_session')

    ######################

    return render(request, 'home.html')

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def select_language(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.email
    if len(settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    global_container = get_global_container()
    languages = global_container.get_languages()

    if not languages:
        return JsonResponse({"error": "Failed to get languages"}, status=500)
    
    return render(request, 'select_language.html',
                  {"languages": languages})

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def get_new_exercise(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)
    user_id = request.user.email
    if len(settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    global_container = get_global_container()

    ######################

    is_subscribed = check_subscription_pipeline(global_container, user_id)

    if not is_subscribed:
        return JsonResponse({"error": "User not subscribed"}, status=403)

    ######################

    (new_exercise,
     success) = global_container.get_new_exercise(user_id)
    
    if not success:
        return JsonResponse({"error": "Failed to get new exercise"}, status=500)
    
    return JsonResponse(new_exercise, status=200)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def get_user_object(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)
    user_id = request.user.email
    if len(settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    global_container = get_global_container()
    
    ######################

    is_subscribed = check_subscription_pipeline(global_container, user_id)

    if not is_subscribed:
        return JsonResponse({"error": "User not subscribed"}, status=403)
    
    ######################
    
    user_object = global_container.get_user_object(user_id)

    if user_object is None:
        return JsonResponse({"error": "Failed to get user object"}, status=500)
    
    return JsonResponse(user_object, status=200)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def submit_answer(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)
    user_id = request.user.email
    if len(settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    global_container = get_global_container()
    
    ######################

    is_subscribed = check_subscription_pipeline(global_container, user_id)

    if not is_subscribed:
        return JsonResponse({"error": "User not subscribed"}, status=403)

    ######################

    data = request.POST
    if not data:
        return JsonResponse({"error": "No data provided"}, status=400)

    exercise_id = data.get("exercise_id")
    answer = data.get("answer")

    if not exercise_id or not answer:
        return JsonResponse({"error": "Missing exercise_id or answer"}, status=400)

    (success, message) = global_container.submit_answer(user_id, 
                                                        exercise_id,
                                                        answer)
    
    if not success:
        return JsonResponse({"error": message}, status=500)
    
    return JsonResponse({"message": message}, status=200)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def get_user_words(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)
    user_id = request.user.email
    if len(settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in settings.OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    global_container = get_global_container()
    
    ######################

    is_subscribed = check_subscription_pipeline(global_container, user_id)

    if not is_subscribed:
        return JsonResponse({"error": "User not subscribed"}, status=403)

    ######################
    
    data = request.GET
    if not data:
        return JsonResponse({"error": "No data provided"}, status=400)
    language = data.get("language")
    is_locked = data.get("is_locked")
    if not language or is_locked is None:
        return JsonResponse({"error": "Missing language or is_locked"}, status=400)
    is_locked = True if is_locked.lower() == "true" else False
    words = global_container.get_user_words(user_id, language, is_locked)

    if words is None:
        return JsonResponse({"error": "Failed to get user words"}, status=500)
    
    return JsonResponse(words, status=200)