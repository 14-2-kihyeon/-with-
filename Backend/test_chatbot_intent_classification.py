"""
챗봇 의도 분류 및 적금 북마크 테스트 시나리오
===================================================

개선 사항:
1. 의도 분류 로직 개선 (예금/적금 vs 주식 명확히 구분)
2. 적금 북마크 기능 추가 (기존에는 예금만 지원)

테스트 방법:
python test_chatbot_intent_classification.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from chatbot.services import ChatbotService
from django.contrib.auth import get_user_model
from accounts.models import InvestmentProfile
from rest_framework.test import APIRequestFactory, force_authenticate
from accounts.views import bookmark_recommendation
from finances.models import DepositProducts, SavingProducts

User = get_user_model()

def test_intent_classification():
    """의도 분류 테스트"""
    print("=" * 80)
    print("테스트 1: 의도 분류 (Intent Classification)")
    print("=" * 80)

    # 테스트용 사용자 가져오기
    user = User.objects.first()
    if not user:
        print("❌ 테스트 사용자 없음")
        return False

    chatbot = ChatbotService(user)

    # 테스트 케이스 정의
    test_cases = [
        # (사용자 메시지, 예상 의도)
        ("안정적인 예금 상품 추천해줘", "PRODUCT"),
        ("금리 높은 적금 알려줘", "PRODUCT"),
        ("원금보장되는 상품 찾아줘", "PRODUCT"),
        ("은행 적금 추천", "PRODUCT"),
        ("삼성전자 주가 어때?", "STOCK"),
        ("카카오 주식 전망은?", "STOCK"),
        ("005930 종목 분석해줘", "STOCK"),
        ("코스피 상승세는?", "STOCK"),
        ("저축 상품 추천해줘", "PRODUCT"),
        ("투자 상품 알려줘", "PRODUCT"),  # 애매하지만 기본값 PRODUCT
    ]

    passed = 0
    failed = 0

    for user_message, expected_intent in test_cases:
        result = chatbot.analyze_user_question(user_message)
        actual_intent = result['intent']

        status = "[PASS]" if actual_intent == expected_intent else "[FAIL]"

        if actual_intent == expected_intent:
            passed += 1
        else:
            failed += 1

        print(f"\n{status}")
        print(f"  입력: '{user_message}'")
        print(f"  예상: {expected_intent}")
        print(f"  실제: {actual_intent}")

    print("\n" + "=" * 80)
    print(f"결과: {passed}개 성공, {failed}개 실패 (총 {len(test_cases)}개)")
    print("=" * 80)

    return failed == 0


def test_critical_case():
    """핵심 케이스: '안정적인 예금 추천' → 절대 주식 추천하면 안됨"""
    print("\n" + "=" * 80)
    print("테스트 2: 핵심 케이스 - '안정적인 예금 상품 추천' → PRODUCT 의도")
    print("=" * 80)

    user = User.objects.first()
    if not user:
        print("❌ 테스트 사용자 없음")
        return False

    chatbot = ChatbotService(user)
    user_message = "안정적인 예금 상품 추천해줘"

    result = chatbot.analyze_user_question(user_message)

    print(f"\n입력: '{user_message}'")
    print(f"분석 결과:")
    print(f"  - 의도: {result['intent']}")
    print(f"  - 종목명: {result['stock_names']}")
    print(f"  - 특정 상품명: {result['specific_product_name']}")

    if result['intent'] == 'PRODUCT':
        print("\n[PASS] 예금/적금 추천 의도로 정확히 분류됨")
        return True
    else:
        print(f"\n[FAIL] 잘못된 의도로 분류됨 ({result['intent']})")
        return False


def test_ambiguous_case():
    """애매한 케이스 테스트: 키워드 없을 때 기본값 확인"""
    print("\n" + "=" * 80)
    print("테스트 3: 애매한 입력 → 기본값 PRODUCT")
    print("=" * 80)

    user = User.objects.first()
    if not user:
        print("❌ 테스트 사용자 없음")
        return False

    chatbot = ChatbotService(user)
    ambiguous_messages = [
        "추천해줘",
        "뭐가 좋아?",
        "도와줘",
    ]

    passed = 0
    for msg in ambiguous_messages:
        result = chatbot.analyze_user_question(msg)

        if result['intent'] == 'PRODUCT':
            print(f"[PASS] '{msg}' -> {result['intent']} (기본값 적용)")
            passed += 1
        else:
            print(f"[FAIL] '{msg}' -> {result['intent']} (기본값 미적용)")

    print(f"\n결과: {passed}/{len(ambiguous_messages)} 통과")
    return passed == len(ambiguous_messages)


def test_deposit_bookmark():
    """예금 북마크 기능 테스트 (기존 기능 유지 확인)"""
    print("\n" + "=" * 80)
    print("테스트 4: 예금 북마크 기능 (기존 기능 유지)")
    print("=" * 80)

    # 사용자 가져오기
    user = User.objects.first()
    if not user:
        print("❌ 테스트 사용자 없음")
        return False

    # 예금 상품 가져오기
    deposit = DepositProducts.objects.first()
    if not deposit:
        print("❌ 예금 상품 없음")
        return False

    print(f"\n테스트 대상: {deposit.fin_prdt_nm} (코드: {deposit.fin_prdt_cd})")

    # API 요청 생성
    factory = APIRequestFactory()
    request = factory.post(f'/api/accounts/bookmark/{deposit.fin_prdt_cd}/')
    force_authenticate(request, user=user)

    # 북마크 추가
    response = bookmark_recommendation(request, deposit.fin_prdt_cd)

    if response.status_code == 200:
        data = response.data
        print(f"\n[PASS] 예금 북마크 성공:")
        print(f"  - 북마크 상태: {data['bookmarked']}")
        print(f"  - 상품 타입: {data['product_type']}")
        print(f"  - 메시지: {data['message']}")
        return True
    else:
        print(f"\n[FAIL] 예금 북마크 실패: {response.status_code}")
        return False


def test_saving_bookmark():
    """적금 북마크 기능 테스트 (새 기능)"""
    print("\n" + "=" * 80)
    print("테스트 5: 적금 북마크 기능 (신규 기능)")
    print("=" * 80)

    # 사용자 가져오기
    user = User.objects.first()
    if not user:
        print("❌ 테스트 사용자 없음")
        return False

    # 적금 상품 가져오기
    saving = SavingProducts.objects.first()
    if not saving:
        print("❌ 적금 상품 없음")
        return False

    print(f"\n테스트 대상: {saving.fin_prdt_nm} (코드: {saving.fin_prdt_cd})")

    # API 요청 생성
    factory = APIRequestFactory()
    request = factory.post(f'/api/accounts/bookmark/{saving.fin_prdt_cd}/')
    force_authenticate(request, user=user)

    # 북마크 추가
    response = bookmark_recommendation(request, saving.fin_prdt_cd)

    if response.status_code == 200:
        data = response.data
        print(f"\n[PASS] 적금 북마크 성공:")
        print(f"  - 북마크 상태: {data['bookmarked']}")
        print(f"  - 상품 타입: {data['product_type']}")
        print(f"  - 메시지: {data['message']}")
        return True
    else:
        print(f"\n[FAIL] 적금 북마크 실패: {response.status_code}")
        print(f"  - 에러: {response.data}")
        return False


def test_bookmark_toggle():
    """북마크 토글 기능 테스트"""
    print("\n" + "=" * 80)
    print("테스트 6: 북마크 토글 (추가 → 제거 → 추가)")
    print("=" * 80)

    user = User.objects.first()
    if not user:
        print("❌ 테스트 사용자 없음")
        return False

    # 다른 적금 상품 사용 (이전 테스트와 겹치지 않게)
    saving = SavingProducts.objects.all()[1] if SavingProducts.objects.count() > 1 else SavingProducts.objects.first()
    if not saving:
        print("❌ 적금 상품 없음")
        return False

    # 기존 북마크 삭제 (깨끗한 상태에서 테스트)
    from accounts.models import SavingRecommendation
    SavingRecommendation.objects.filter(user=user, product=saving).delete()

    factory = APIRequestFactory()

    # 1. 첫 번째 북마크 (추가)
    request1 = factory.post(f'/api/accounts/bookmark/{saving.fin_prdt_cd}/')
    force_authenticate(request1, user=user)
    response1 = bookmark_recommendation(request1, saving.fin_prdt_cd)

    # 2. 두 번째 북마크 (제거)
    request2 = factory.post(f'/api/accounts/bookmark/{saving.fin_prdt_cd}/')
    force_authenticate(request2, user=user)
    response2 = bookmark_recommendation(request2, saving.fin_prdt_cd)

    # 3. 세 번째 북마크 (다시 추가)
    request3 = factory.post(f'/api/accounts/bookmark/{saving.fin_prdt_cd}/')
    force_authenticate(request3, user=user)
    response3 = bookmark_recommendation(request3, saving.fin_prdt_cd)

    bookmarked_1 = response1.data['bookmarked']
    bookmarked_2 = response2.data['bookmarked']
    bookmarked_3 = response3.data['bookmarked']

    print(f"\n토글 결과:")
    print(f"  1회차: {bookmarked_1} (추가)")
    print(f"  2회차: {bookmarked_2} (제거)")
    print(f"  3회차: {bookmarked_3} (추가)")

    # 토글이 정상 작동했는지 확인
    if bookmarked_1 == True and bookmarked_2 == False and bookmarked_3 == True:
        print("\n[PASS] 북마크 토글 정상 작동")
        return True
    else:
        print("\n[FAIL] 북마크 토글 비정상")
        return False


def run_all_tests():
    """모든 테스트 실행"""
    print("\n")
    print("=" * 80)
    print(" " * 20 + "챗봇 개선 테스트 시작")
    print("=" * 80)

    results = []

    # 의도 분류 테스트
    results.append(("의도 분류", test_intent_classification()))

    # 핵심 케이스 테스트
    results.append(("핵심 케이스 (안정적인 예금)", test_critical_case()))

    # 애매한 케이스 테스트
    results.append(("애매한 입력 기본값", test_ambiguous_case()))

    # 예금 북마크 테스트
    results.append(("예금 북마크", test_deposit_bookmark()))

    # 적금 북마크 테스트
    results.append(("적금 북마크", test_saving_bookmark()))

    # 북마크 토글 테스트
    results.append(("북마크 토글", test_bookmark_toggle()))

    # 결과 요약
    print("\n")
    print("=" * 80)
    print(" " * 30 + "최종 결과")
    print("=" * 80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 80)
    print(f"전체 결과: {passed_count}/{total_count} 성공")

    if passed_count == total_count:
        print("\n[SUCCESS] 모든 테스트 통과! 챗봇 개선 성공!")
    else:
        print(f"\n[WARNING] {total_count - passed_count}개 테스트 실패")

    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
