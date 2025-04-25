from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib.auth.decorators import login_required

from django_ratelimit.decorators import ratelimit

DEFAULT_RATELIMIT = '100/h'  # Default rate limit for all views

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
def login_view(request):

    if request.user.is_authenticated:
        return redirect('player')  # or your desired post-login view

    return render(request, 'login.html')

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def home(request):
    return render(request, 'home.html')

# def home(request):
#     # # ...
#     # if 1:
#     #     return HttpResponseNotFound("<h1>Page not found</h1>")
#     # else:
#     #     return HttpResponse("<h1>Page was found</h1>")

#     return render(request, "home.html")#, {"var": 1})

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def player(request):
    return render(request, "player.html")#, {"var": 1})

@ratelimit(key='ip', rate=DEFAULT_RATELIMIT)
@login_required
def settings(request):
    return render(request, "settings.html")#, {"var": 1})