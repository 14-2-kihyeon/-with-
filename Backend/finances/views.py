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

# ============================================
# 예금
# ============================================

@api_view(["GET", "POST"])  # ✅ GET도 허용
@permission_classes([AllowAny])  # ✅ 누구나 호출 가능
def sync_deposits(request):
    """
    금융감독원 API에서 예금 데이터를 가져와 DB에 저장
    GET/POST /finances/deposits/sync/
    """
    try:
        print("📡 예금 데이터 동기화 시작...")
        data = fetch_deposit_products()
        
        if not data:
            return Response(
                {"error": "API 호출 실패"}, 
                status=status.HTTP_502_BAD_GATEWAY
            )

        saved_products = 0
        saved_options = 0

        # 상품 저장
        for prod in data.get("baseList", []):
            product, created = DepositProducts.objects.update_or_create(
                fin_prdt_cd=prod["fin_prdt_cd"],
                defaults={
                    "kor_co_nm": prod.get("kor_co_nm", ""),
                    "fin_prdt_nm": prod.get("fin_prdt_nm", ""),
                    "join_way": prod.get("join_way"),
                    "join_deny": prod.get("join_deny", 1),
                    "join_member": prod.get("join_member"),
                    "spcl_cnd": prod.get("spcl_cnd"),
                }
            )
            if created:
                saved_products += 1

        # 옵션 저장
        for opt in data.get("optionList", []):
            try:
                product = DepositProducts.objects.get(fin_prdt_cd=opt["fin_prdt_cd"])
                
                # intr_rate 처리 (None이면 -1)
                intr_rate = opt.get("intr_rate")
                intr_rate2 = opt.get("intr_rate2")
                
                if intr_rate is None or intr_rate == "":
                    intr_rate = -1
                if intr_rate2 is None or intr_rate2 == "":
                    intr_rate2 = -1
                
                option, created = DepositOptions.objects.update_or_create(
                    product=product,
                    save_trm=opt.get("save_trm", 0),
                    rsrv_type=opt.get("rsrv_type"),
                    defaults={
                        "intr_rate": float(intr_rate),
                        "intr_rate2": float(intr_rate2),
                    }
                )
                if created:
                    saved_options += 1
                    
            except DepositProducts.DoesNotExist:
                print(f"⚠️  상품 없음: {opt.get('fin_prdt_cd')}")
                continue
            except Exception as e:
                print(f"❌ 옵션 저장 실패: {e}")
                continue

        print(f"✅ 저장 완료: 상품 {saved_products}개, 옵션 {saved_options}개")
        
        return Response({
            "message": "동기화 완료",
            "saved_products": saved_products,
            "saved_options": saved_options,
            "total_products": DepositProducts.objects.count(),
            "total_options": DepositOptions.objects.count(),
        })
        
    except Exception as e:
        import traceback
        print(f"❌ 동기화 실패: {e}")
        traceback.print_exc()
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def bank_list(request):
    """은행 목록 조회"""
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
    """예금 상품 목록 조회"""
    bank = request.GET.get("bank")
    qs = DepositProducts.objects.all().order_by("kor_co_nm", "fin_prdt_nm")
    
    if bank:
        qs = qs.filter(kor_co_nm=bank)

    serializer = DepositProductListSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def deposit_detail(request, fin_prdt_cd):
    """예금 상품 상세 조회"""
    product = DepositProducts.objects.filter(fin_prdt_cd=fin_prdt_cd).first()
    
    if not product:
        return Response(
            {"detail": "상품을 찾을 수 없습니다."}, 
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = DepositProductDetailSerializer(product)
    return Response(serializer.data)


# ============================================
# 적금
# ============================================

@api_view(["GET", "POST"])  # ✅ GET도 허용
@permission_classes([AllowAny])  # ✅ 누구나 호출 가능
def sync_savings(request):
    """
    금융감독원 API에서 적금 데이터를 가져와 DB에 저장
    GET/POST /finances/savings/sync/
    """
    try:
        print("📡 적금 데이터 동기화 시작...")
        data = fetch_saving_products()
        
        if not data:
            return Response(
                {"error": "API 호출 실패"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        saved_products = 0
        saved_options = 0

        # 상품 저장
        for prod in data.get("baseList", []):
            product, created = SavingProducts.objects.update_or_create(
                fin_prdt_cd=prod["fin_prdt_cd"],
                defaults={
                    "kor_co_nm": prod.get("kor_co_nm", ""),
                    "fin_prdt_nm": prod.get("fin_prdt_nm", ""),
                    "join_way": prod.get("join_way"),
                    "join_deny": prod.get("join_deny", 1),
                    "join_member": prod.get("join_member"),
                    "spcl_cnd": prod.get("spcl_cnd"),
                    "mtrt_int": prod.get("mtrt_int"),
                }
            )
            if created:
                saved_products += 1

        # 옵션 저장
        for opt in data.get("optionList", []):
            product = SavingProducts.objects.filter(
                fin_prdt_cd=opt["fin_prdt_cd"]
            ).first()
            
            if not product:
                continue

            # intr_rate 처리
            intr_rate = opt.get("intr_rate")
            intr_rate2 = opt.get("intr_rate2")
            
            if intr_rate is None or intr_rate == "":
                intr_rate = -1
            if intr_rate2 is None or intr_rate2 == "":
                intr_rate2 = -1

            option, created = SavingOptions.objects.update_or_create(
                product=product,
                save_trm=int(opt.get("save_trm", 0)),
                rsrv_type=opt.get("rsrv_type"),
                intr_rate_type=opt.get("intr_rate_type"),
                defaults={
                    "intr_rate": float(intr_rate),
                    "intr_rate2": float(intr_rate2),
                    "rsrv_type_nm": opt.get("rsrv_type_nm"),
                    "intr_rate_type_nm": opt.get("intr_rate_type_nm"),
                }
            )
            if created:
                saved_options += 1

        print(f"✅ 저장 완료: 상품 {saved_products}개, 옵션 {saved_options}개")
        
        return Response({
            "message": "적금 동기화 완료",
            "saved_products": saved_products,
            "saved_options": saved_options,
            "total_products": SavingProducts.objects.count(),
            "total_options": SavingOptions.objects.count(),
        })
        
    except Exception as e:
        import traceback
        print(f"❌ 동기화 실패: {e}")
        traceback.print_exc()
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def saving_bank_list(request):
    """적금 은행 목록"""
    banks = (
        SavingProducts.objects
        .values_list("kor_co_nm", flat=True)
        .distinct()
        .order_by("kor_co_nm")
    )
    return Response(list(banks))


@api_view(["GET"])
@permission_classes([AllowAny])
def saving_list(request):
    """적금 상품 목록"""
    bank = request.GET.get("bank")
    qs = SavingProducts.objects.all().order_by("kor_co_nm", "fin_prdt_nm")
    
    if bank:
        qs = qs.filter(kor_co_nm=bank)

    serializer = SavingProductsSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def saving_detail(request, fin_prdt_cd):
    """적금 상품 상세"""
    product = SavingProducts.objects.filter(fin_prdt_cd=fin_prdt_cd).first()
    
    if not product:
        return Response(
            {"error": "상품을 찾을 수 없습니다."}, 
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = SavingProductsSerializer(product)
    return Response(serializer.data)