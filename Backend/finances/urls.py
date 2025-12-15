from django.urls import path
from . import views

app_name = "finances"

urlpatterns = [
    # (선택) 외부 API -> DB 저장(동기화). 화면에서 자주 안 씀
    path("deposits/sync/", views.sync_deposits, name="sync_deposits"),
    path("savings/sync/", views.sync_savings, name="sync_savings"),

    # ✅ 화면에서 사용할 GET들
    path("banks/", views.bank_list, name="bank_list"),
    path("deposits/", views.deposit_list, name="deposit_list"),  # ?bank=국민은행
    path("deposits/<str:fin_prdt_cd>/", views.deposit_detail, name="deposit_detail"),

    path("savings/banks/", views.saving_bank_list, name="saving_bank_list"),
    path("savings/", views.saving_list, name="saving_list"),
    path("savings/<str:fin_prdt_cd>/", views.saving_detail, name="saving_detail"),  
]