from django.urls import path
from . import views

urlpatterns = [
    path("search/", views.search_view),
    path("videos/<str:video_id>/", views.detail_view),
]