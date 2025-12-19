from django.urls import path
from . import views

urlpatterns = [
    path("route/", views.route, name="kakao-route"),
]
