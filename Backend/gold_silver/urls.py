from django.urls import path
from . import views

urlpatterns = [
    path('get_price_data/', views.get_price_data, name='get_price_data'),
]