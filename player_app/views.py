from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib.auth.decorators import login_required

def login_view(request):
    return render(request, 'login.html')

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

@login_required
def player(request):
    return render(request, "player.html")#, {"var": 1})

@login_required
def settings(request):
    return render(request, "settings.html")#, {"var": 1})