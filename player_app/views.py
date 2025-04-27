
import datetime

import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

from django_ratelimit.decorators import ratelimit

try:
    from language_app_backend.util.db import get_global_container
    from language_app_backend.util.constants import (CHECK_SUBSCRIPTION_INTERVAL, 
                                                     DO_NOT_CHECK_SUBSCRIPTION,
                                                     DEFAULT_RATELIMIT,
                                                     OPEN_LANGUAGE_APP_ALLOWED_USER_IDS)
except ImportError:
    print("ImportError: language_app_backend not found. ")

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

    if DO_NOT_CHECK_SUBSCRIPTION:
        return True

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
    
    if DO_NOT_CHECK_SUBSCRIPTION:
        return redirect('settings')

    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='subscription',
        line_items=[{
            'price': settings.STRIPE_PRICE_ID,  # We'll set this in a minute
            'quantity': 1,
        }],
        success_url=f'{settings.FRONTEND_URL}/settings?session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url=f'{settings.FRONTEND_URL}/settings',
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

    if DO_NOT_CHECK_SUBSCRIPTION:
        return redirect('settings')

    customers = stripe.Customer.list(email=request.user.email).data
    if not customers:
        return redirect('settings')  # fallback if no customer found
    customer = customers[0]

    session = stripe.billing_portal.Session.create(
        customer=customer.id,
        return_url=f'{settings.FRONTEND_URL}/settings',
    )
    return redirect(session.url)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def app_settings(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
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
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    
    global_container = get_global_container()
    
    # check if language is set
    language = global_container.get_user_language(user_id)

    if language is None:

        data = request.GET
        if not data:
            return redirect('select_language')
        
        language = data.get("language")
        if not language:
            return redirect('select_language')
        
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
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    global_container = get_global_container()
    languages = global_container.get_languages()

    if not languages:
        return JsonResponse({"error": "Failed to get languages"}, status=500)
    
    return render(request, 'select_language.html',
                  {"languages": languages})

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def get_created_exercise(request):
    print("extra debug 0")
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)
    print("extra debug 1")
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    print("extra debug 2")
    global_container = get_global_container()

    ######################

    print("extra debug 3")
    is_subscribed = check_subscription_pipeline(global_container, user_id)

    if not is_subscribed:
        return JsonResponse({"error": "User not subscribed"}, status=403)
    print("extra debug 4")

    ######################
    print("extra debug 5")

    (exercise, 
     success) = global_container.get_created_exercise(user_id)
    
    print("extra debug 6")
    if not success:
        return JsonResponse({"error": "Failed to get created exercise"}, status=500)
    
    print("extra debug 7")
    if exercise is not None:

        print(f"Exercise: {exercise}")

        # Exercise: {'_id': ObjectId('680e813128a089206d8359ba'), 
        #            'exercise_id': '7f4ae423-48da-4cce-bb20-a9e9f6ed7938', 
        #            'created_at': 1745781041, 'criteria': 2, 
        #            'exercise_type': '2_1', 
        #            'final_strings': ['a) Cuándo / cuándo', 'b) Cuando / cuando', 'c) Cuándo / cuando', 'd) Cuando / cuándo'], 
        #            'initial_strings': ['___ ___ estudias, te concentras mejor.'], 'language': 'es', 'level': 0, 
        #            'middle_strings': ['Choose the correct first two words:'], 
        #            'word_keys': ['1dba0d60-e5e5-413c-b719-8194f2293df7', '1dba0d60-e5e5-413c-b719-8194f2293df7'], 
        #            'word_values': ['cuando', 'cuando']}
        
        exercise = {
            "exercise_id": exercise.get("exercise_id", ""),
            "initial_strings": list(exercise.get("initial_strings", [])),
            "middle_strings": list(exercise.get("middle_strings", [])),
            "final_strings": list(exercise.get("final_strings", []),)
        }
        
        print("extra debug 8")
        return JsonResponse({"success": True,
                            "exercise": exercise}, status=200)
    else:
        print("No exercise created yet.")
        return JsonResponse({"success": True}, status=200)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def create_new_exercise(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    global_container = get_global_container()

    ######################

    is_subscribed = check_subscription_pipeline(global_container, user_id)

    if not is_subscribed:
        return JsonResponse({"error": "User not subscribed"}, status=403)

    ######################

    success = global_container.create_new_exercise(user_id)
    
    if not success:
        return JsonResponse({"error": "Failed to get new exercise"}, status=500)
    
    return JsonResponse({"success": True,
                         "message": "A new exercise is being created."}, status=200)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def get_user_object(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
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
    
    return JsonResponse({"success": True,
                         "user": user_object}, status=200)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def apply_thumbs_up_or_down(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    global_container = get_global_container()

    #######################

    is_subscribed = check_subscription_pipeline(global_container, user_id)

    if not is_subscribed:
        return JsonResponse({"error": "User not subscribed"}, status=403)
    
    #######################

    data = request.GET
    if not data:
        return JsonResponse({"error": "No data provided"}, status=400)
    
    exercise_id = data.get("exercise_id")
    thumbs_up = data.get("is_positive")

    if not exercise_id or not thumbs_up:
        return JsonResponse({"error": "Missing exercise_id or thumbs_up"}, status=400)
    
    thumbs_up = True if thumbs_up.lower() == "true" else False

    success = global_container.apply_thumbs_up_or_down(user_id,
                                                        exercise_id, 
                                                        thumbs_up)
    
    return JsonResponse({"success": success}, status=200)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def submit_answer(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
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

    exercise_id = data.get("exercise_id")
    answer = data.get("answer")

    if not exercise_id or not answer:
        return JsonResponse({"error": "Missing exercise_id or answer"}, status=400)

    (success, 
     message,
     correct) = global_container.submit_answer(user_id, 
                                                exercise_id,
                                                answer)
    
    if not success:
        return JsonResponse({"error": message}, status=500)
    
    return JsonResponse({"success": True,
                         "message": message,
                         "correct": correct}, status=200)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def get_user_words(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
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