from django.urls import path
from . import views

urlpatterns = [
    path("save/", views.save_deposit_products),  # F01
    path("products/", views.deposit_products_list),  # F02
    path("products/add/", views.add_deposit_product),  # F03
    path("options/<str:fin_prdt_cd>/", views.deposit_product_options),  # F04
    path("highest/", views.highest_intr_rate_product),  # F05
]
