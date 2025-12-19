from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from .models import DepositProducts, DepositOptions, SavingProducts, SavingOptions
from .serializers import (
    DepositProductListSerializer,
    DepositProductDetailSerializer,
    SavingProductsSerializer
)
from .utils import fetch_deposit_products, fetch_saving_products

# 예금

@api_view(["POST"])
@permission_classes([IsAuthenticated])   # 원하면 AllowAny로 바꿔도 됨(비추천)
def sync_deposits(request):
    data = fetch_deposit_products()

    # 상품 저장
    for prod in data["baseList"]:
        DepositProducts.objects.update_or_create(
            fin_prdt_cd=prod["fin_prdt_cd"],
            defaults={
                "kor_co_nm": prod["kor_co_nm"],
                "fin_prdt_nm": prod["fin_prdt_nm"],
                "join_way": prod.get("join_way"),
                "join_deny": prod.get("join_deny", 1),
                "join_member": prod.get("join_member"),
                "spcl_cnd": prod.get("spcl_cnd"),
            }
        )

    # 옵션 저장
    for opt in data["optionList"]:
        product = DepositProducts.objects.get(fin_prdt_cd=opt["fin_prdt_cd"])
        DepositOptions.objects.update_or_create(
            product=product,
            save_trm=opt["save_trm"],
            defaults={
                "intr_rate": opt.get("intr_rate", -1),
                "intr_rate2": opt.get("intr_rate2", -1),
                "rsrv_type": opt.get("rsrv_type"),
            }
        )

    return Response({"message": "sync ok"})


@api_view(["GET"])
@permission_classes([AllowAny])
def bank_list(request):
    banks = (
        DepositProducts.objects
        .values_list("kor_co_nm", flat=True)
        .distinct()
        .order_by("kor_co_nm")
    )
    return Response(list(banks))


@api_view(["GET"])
@permission_classes([AllowAny])
def deposit_list(request):
    bank = request.GET.get("bank")  # 예: ?bank=국민은행
    qs = DepositProducts.objects.all().order_by("kor_co_nm", "fin_prdt_nm")
    if bank:
        qs = qs.filter(kor_co_nm=bank)

    serializer = DepositProductListSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def deposit_detail(request, fin_prdt_cd):
    product = DepositProducts.objects.filter(fin_prdt_cd=fin_prdt_cd).first()
    if not product:
        return Response({"detail": "not found"}, status=404)

    serializer = DepositProductDetailSerializer(product)
    return Response(serializer.data)




# 적금

@api_view(["GET"])
def sync_savings(request):
    data = fetch_saving_products()
    if not data:
        return Response({"error": "API 호출 실패"}, status=status.HTTP_400_BAD_REQUEST)

    # 상품
    for prod in data.get("baseList", []):
        SavingProducts.objects.update_or_create(
            fin_prdt_cd=prod["fin_prdt_cd"],
            defaults={
                "kor_co_nm": prod["kor_co_nm"],
                "fin_prdt_nm": prod["fin_prdt_nm"],
                "join_way": prod.get("join_way"),
                "join_deny": prod.get("join_deny", 1),
                "join_member": prod.get("join_member"),
                "spcl_cnd": prod.get("spcl_cnd"),
                "mtrt_int": prod.get("mtrt_int"),
            }
        )

    # 옵션
    for opt in data.get("optionList", []):
        product = SavingProducts.objects.filter(fin_prdt_cd=opt["fin_prdt_cd"]).first()
        if not product:
            continue

        # save_trm + rsrv_type + intr_rate_type 정도까지 묶어야 옵션 중복이 덜함
        SavingOptions.objects.update_or_create(
            product=product,
            save_trm=int(opt.get("save_trm", 0)),
            rsrv_type=opt.get("rsrv_type"),
            intr_rate_type=opt.get("intr_rate_type"),
            defaults={
                "intr_rate": opt.get("intr_rate", -1) if opt.get("intr_rate") is not None else -1,
                "intr_rate2": opt.get("intr_rate2", -1) if opt.get("intr_rate2") is not None else -1,
                "rsrv_type_nm": opt.get("rsrv_type_nm"),
                "intr_rate_type_nm": opt.get("intr_rate_type_nm"),
            }
        )

    return Response({"message": "적금 저장 완료"})


@api_view(["GET"])
def saving_bank_list(request):
    banks = SavingProducts.objects.values_list("kor_co_nm", flat=True).distinct().order_by("kor_co_nm")
    return Response(list(banks))


@api_view(["GET"])
def saving_list(request):
    bank = request.GET.get("bank")
    qs = SavingProducts.objects.all().order_by("kor_co_nm", "fin_prdt_nm")
    if bank:
        qs = qs.filter(kor_co_nm=bank)

    serializer = SavingProductsSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def saving_detail(request, fin_prdt_cd):
    product = SavingProducts.objects.filter(fin_prdt_cd=fin_prdt_cd).first()
    if not product:
        return Response({"error": "상품 없음"}, status=404)

    serializer = SavingProductsSerializer(product)
    return Response(serializer.data)