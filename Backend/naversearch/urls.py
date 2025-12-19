# naversearch/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("news/search/", views.news_search),
    path("news/", views.news_list),
    path("news/<int:pk>/", views.news_detail),
    path("news/<int:pk>/bookmark/", views.toggle_bookmark),
    path("news/<int:pk>/summary/", views.summarize_news),
]
