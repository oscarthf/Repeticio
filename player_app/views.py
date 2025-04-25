from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound

def home(request):
    # # ...
    # if 1:
    #     return HttpResponseNotFound("<h1>Page not found</h1>")
    # else:
    #     return HttpResponse("<h1>Page was found</h1>")

    return render(request, "home.html", {"var": 1})

def player(request):
    return render(request, "player.html", {"var": 1})