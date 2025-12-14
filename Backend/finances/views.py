from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import DepositProducts, DepositOptions
from .serializers import DepositProductsSerializer, DepositOptionsSerializer
from .utils import fetch_deposit_products

# -----------------------
# F01: 외부 API 데이터 수집 후 DB 저장
# -----------------------
@api_view(['GET'])
def save_deposit_products(request):
    data = fetch_deposit_products()

    # 상품 저장
    for prod in data["baseList"]:
        product, _ = DepositProducts.objects.update_or_create(
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
        DepositOptions.objects.update_or_create(
            product=DepositProducts.objects.get(fin_prdt_cd=opt["fin_prdt_cd"]),
            save_trm=opt["save_trm"],
            defaults={
                "intr_rate": opt.get("intr_rate", -1),
                "intr_rate2": opt.get("intr_rate2", -1),
                "rsrv_type": opt.get("rsrv_type"),
            }
        )

    return Response({"message": "저장 완료"})


# -----------------------
# F02: 전체 상품 목록 조회
# -----------------------
@api_view(['GET'])
def deposit_products_list(request):
    qs = DepositProducts.objects.all()
    serializer = DepositProductsSerializer(qs, many=True)
    return Response(serializer.data)


# -----------------------
# F03: 상품 직접 추가
# -----------------------
@api_view(['POST'])
def add_deposit_product(request):
    serializer = DepositProductsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "데이터 삽입 성공"})
    return Response(serializer.errors, status=400)


# -----------------------
# F04: 특정 상품 옵션 조회
# -----------------------
@api_view(['GET'])
def deposit_product_options(request, fin_prdt_cd):
    product = DepositProducts.objects.filter(fin_prdt_cd=fin_prdt_cd).first()
    if not product:
        return Response({"error": "상품을 찾을 수 없음"}, status=404)

    options = DepositOptions.objects.filter(product=product)
    serializer = DepositOptionsSerializer(options, many=True)
    return Response(serializer.data)


# -----------------------
# F05: 최고 금리 상품 조회
# -----------------------
@api_view(['GET'])
def highest_intr_rate_product(request):
    option = DepositOptions.objects.order_by('-intr_rate2').first()

    if not option:
        return Response({"error": "데이터 없음"}, status=404)

    product = option.product
    return Response({
        "product": DepositProductsSerializer(product).data,
        "option": DepositOptionsSerializer(option).data
    })
