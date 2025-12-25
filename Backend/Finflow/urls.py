
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/registration/", include("dj_rest_auth.registration.urls")),
    path("accounts/", include("dj_rest_auth.urls")),
    
    path('accounts/', include('accounts.urls')),
    
    path('finances/', include('finances.urls')),
    path('posts/', include('posts.urls')),
    path("naver/", include("naversearch.urls")),
    path("kakaomap/", include('kakaomap.urls')),
    path("youtube/", include('youtube.urls')),
    path("gold_silver/", include('gold_silver.urls')),
    path('api/stocks/', include('stocks.urls')),
    path('chatbot/', include('chatbot.urls')),

]
