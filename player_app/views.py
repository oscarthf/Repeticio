
import json

import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required

from django_ratelimit.decorators import ratelimit

from player_app.APIClient import RepeticioAPIClient

stripe.api_key = settings.STRIPE_SECRET_KEY

repeticio_api = RepeticioAPIClient(settings.REPETICIO_API_BASE_URL)

# OPEN_LANGUAGE_APP_ALLOWED_USER_IDS = ["your_whitelisted_email@gmail.com"]
OPEN_LANGUAGE_APP_ALLOWED_USER_IDS = []
GET_CREATED_EXERCISES_RATELIMIT = '40/m'  # Rate limit for get_created_exercises view
DEFAULT_RATELIMIT = '100/h'  # Default rate limit for all views

DO_NOT_CHECK_SUBSCRIPTION = repeticio_api.get_do_not_check_subscription()

##########################################################################
### DOES NOT NEED SUBSCRIPTION ###########################################
##########################################################################

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
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
            'price': settings.STRIPE_PRICE_ID,
            'quantity': 1,
        }],
        success_url=f'{settings.FRONTEND_URL}/settings?session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url=f'{settings.FRONTEND_URL}/settings',
        customer_email=request.user.email,
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

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_email')

        repeticio_api.set_user_subscription(customer_email, True)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription['customer']

        # Find email by customer ID
        customer = stripe.Customer.retrieve(customer_id)
        customer_email = customer.email

        if customer_email:
            repeticio_api.set_user_subscription(customer_email, False)

    return HttpResponse(status=200)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def customer_portal(request):

    if DO_NOT_CHECK_SUBSCRIPTION:
        return redirect('settings')

    customers = stripe.Customer.list(email=request.user.email).data
    if not customers:
        return redirect('settings')# fallback if no customer found
    customer = customers[0]

    session = stripe.billing_portal.Session.create(
        customer=customer.id,
        return_url=f'{settings.FRONTEND_URL}/settings',
    )
    return redirect(session.url)

##########################################################################
### DOES NEED SUBSCRIPTION ###############################################
##########################################################################

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def app_settings(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)

    ######################

    is_subscribed = repeticio_api.check_subscription_pipeline(user_id)

    if not is_subscribed:
        return redirect('create_checkout_session')

    ######################

    user_object = repeticio_api.get_user_object(user_id)
    if user_object is None:
        user_object = {}

    ######################

    learning_language = repeticio_api.get_learning_language(user_id)

    if learning_language is None:
        return redirect('select_learning_language')
    
    user_words = repeticio_api.get_user_words(user_id, 
                                                 learning_language, 
                                                 False)
    
    if user_words is None:
        user_words = []
    
    ######################

    user_words_no_ids = []

    for word in user_words:
        # word = {
        #     "word_id": word_id,
        #     "user_id": user_id,
        #     "word_value": word_value,
        #     "language": language,
        #     "last_visited_times": [],
        #     "last_scores": [],
        #     "is_locked": True
        # }

        word_no_id = {
            "word_value": word.get("word_value", ""),
            "language": word.get("language", ""),
            "last_visited_times": list(word.get("last_visited_times", [])),
            "last_scores": list(word.get("last_scores", [])),
            "is_locked": word.get("is_locked", True)
        }

        user_words_no_ids.append(word_no_id)

    del user_object["_id"]

    user_object_json = json.dumps(user_object, ensure_ascii=False)
    user_words_json = json.dumps(user_words_no_ids, ensure_ascii=False)

    return render(request, "settings.html", {"user_object_json": user_object_json,
                                             "user_words_json": user_words_json})

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    
    ######################

    did_create_user = repeticio_api.create_user_if_needed(user_id)

    success, redirect_view = repeticio_api.redirect_if_new_user(user_id)
    
    if not success:# could be "select_ui_language" or "select_learning_language"
        return redirect(redirect_view)
    
    ######################

    is_subscribed = repeticio_api.check_subscription_pipeline(user_id)

    if not is_subscribed:
        return redirect('create_checkout_session')

    ######################

    return render(request, 'home.html', {"show_ads": True,
                                         "google_adsense_client_id": settings.GOOGLE_ADSENSE_CLIENT_ID})

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def select_ui_language(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    
    did_create_user = repeticio_api.create_user_if_needed(user_id)

    supported_languages = repeticio_api.get_supported_languages()

    if not supported_languages:
        return JsonResponse({"error": "Failed to get supported_languages"}, status=500)
    
    return render(request, 'select_language.html',
                  {"languages": supported_languages,
                   "title_string": "What language would you like instructions in?",
                   "is_set_ui_language": "true"})

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def select_learning_language(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    
    did_create_user = repeticio_api.create_user_if_needed(user_id)

    supported_languages = repeticio_api.get_supported_languages()

    if not supported_languages:
        return JsonResponse({"error": "Failed to get supported_languages"}, status=500)
    
    return render(request, 'select_language.html',
                  {"languages": supported_languages,
                   "title_string": "What language would you like to practice?",
                   "is_set_ui_language": "false"})

@ratelimit(key='ip', rate=GET_CREATED_EXERCISES_RATELIMIT)
@login_required
def get_created_exercise(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)

    ######################

    is_subscribed = repeticio_api.check_subscription_pipeline(user_id)

    if not is_subscribed:
        return JsonResponse({"error": "User not subscribed"}, status=403)

    ######################

    (exercise, 
     success) = repeticio_api.get_created_exercise(user_id)
    
    if not success:
        return JsonResponse({"error": "Failed to get created exercise"}, status=500)
    
    if exercise is not None:

        print(f"Exercise: {exercise}")

        exercise = {
            "exercise_id": exercise.get("exercise_id", ""),
            "initial_strings": list(exercise.get("initial_strings", [])),
            "middle_strings": list(exercise.get("middle_strings", [])),
            "final_strings": list(exercise.get("final_strings", []),)
        }
        
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

    ######################

    is_subscribed = repeticio_api.check_subscription_pipeline(user_id)

    if not is_subscribed:
        return JsonResponse({"error": "User not subscribed"}, status=403)

    ######################

    success = repeticio_api.create_new_exercise(user_id)
    
    if not success:
        return JsonResponse({"error": "Failed to get new exercise"}, status=500)
    
    return JsonResponse({"success": True,
                         "message": "A new exercise is being created."}, status=200)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def apply_thumbs_up_or_down(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)

    #######################

    is_subscribed = repeticio_api.check_subscription_pipeline(user_id)

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

    success = repeticio_api.apply_thumbs_up_or_down(user_id,
                                                        exercise_id, 
                                                        thumbs_up)
    
    return JsonResponse({"success": success}, status=200)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def set_learning_language(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)

    data = request.GET

    if not data:
        return JsonResponse({"error": "No data provided"}, status=400)
    
    if not data.get("language"):
        return JsonResponse({"error": "Missing language"}, status=400)
    
    learning_language = data.get("language")

    success = repeticio_api.set_learning_language(user_id, learning_language)
    if not success:
        return JsonResponse({"error": "Failed to set learning language"}, status=500)
    
    return JsonResponse({"success": True,
                         "message": "Learning language set successfully"}, status=200)
    
@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def set_ui_language(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)

    data = request.GET

    if not data:
        return JsonResponse({"error": "No data provided"}, status=400)
    
    if not data.get("language"):
        return JsonResponse({"error": "Missing language"}, status=400)
    
    ui_language = data.get("language")

    success = repeticio_api.set_ui_language(user_id, ui_language)
    if not success:
        return JsonResponse({"error": "Failed to set UI language"}, status=500)
    
    return JsonResponse({"success": True,
                         "message": "UI language set successfully"}, status=200)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def submit_answer(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)
    user_id = request.user.email
    if len(OPEN_LANGUAGE_APP_ALLOWED_USER_IDS) and user_id not in OPEN_LANGUAGE_APP_ALLOWED_USER_IDS:
        return HttpResponse("You are not allowed to access this page.", status=403)
    
    ######################

    is_subscribed = repeticio_api.check_subscription_pipeline(user_id)

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
     correct) = repeticio_api.submit_answer(user_id, 
                                                exercise_id,
                                                answer)
    
    if not success:
        return JsonResponse({"error": message}, status=500)
    
    return JsonResponse({"success": True,
                         "message": message,
                         "correct": correct}, status=200)
