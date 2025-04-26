
import uuid

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from django_ratelimit.decorators import ratelimit

from language_app_backend.util.db import get_global_container

DEFAULT_RATELIMIT = '100/h'  # Default rate limit for all views

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # or your desired post-login view

    return render(request, 'login.html')

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.id
    global_container = get_global_container()
    global_container.create_user_if_not_exists(user_id)

    return render(request, 'home.html')

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def settings(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user_id = request.user.id
    return render(request, "settings.html", {"user_id": user_id})

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def get_new_exercise(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)
    user_id = request.user.id
    global_container = get_global_container()
    (new_exercise,
     success) = global_container.get_new_exercise(user_id)
    
    if not success:
        return JsonResponse({"error": "Failed to get new exercise"}, status=500)
    
    return JsonResponse(new_exercise, status=200)

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def submit_answer(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)
    user_id = request.user.id
    global_container = get_global_container()
    data = request.POST

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
