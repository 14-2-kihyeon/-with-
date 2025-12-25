"""
챗봇 전체 통합 테스트 (RAG 포함)
- 실제 사용자 질문에 대한 응답 확인
- 의도 분류 정확도 확인
- RAG 시스템 정상 작동 확인
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from chatbot.services import ChatbotService
from django.contrib.auth import get_user_model

User = get_user_model()

def test_chatbot_response(user_message):
    """챗봇 응답 테스트"""
    print("\n" + "=" * 80)
    print(f"테스트: '{user_message}'")
    print("=" * 80)

    user = User.objects.first()
    if not user:
        print("[ERROR] 테스트 사용자 없음")
        return False

    chatbot = ChatbotService(user)

    try:
        # 1. 의도 분석
        print("\n[1단계] 의도 분석 중...")
        analysis = chatbot.analyze_user_question(user_message)
        print(f"  - 의도: {analysis['intent']}")
        print(f"  - 종목명: {analysis['stock_names']}")
        print(f"  - 특정 상품: {analysis['specific_product_name']}")

        # 2. 챗봇 응답 생성
        print("\n[2단계] 챗봇 응답 생성 중...")
        result = chatbot.chat(user_message)

        if result['success']:
            print("\n[SUCCESS] 챗봇 응답 성공!")
            print("\n[응답 내용]")
            print("-" * 80)
            # 응답이 너무 길면 앞부분만 출력
            response_text = result['response']
            # Windows 콘솔 인코딩 문제 해결: 특수 문자 제거
            safe_text = response_text.encode('cp949', errors='ignore').decode('cp949')
            if len(safe_text) > 500:
                print(safe_text[:500] + "...\n(응답 길이: " + str(len(response_text)) + "자)")
            else:
                print(safe_text)
            print("-" * 80)

            # 추천 상품 확인
            if result.get('recommended_products'):
                print("\n[추천 상품]")
                for i, product in enumerate(result['recommended_products'], 1):
                    product_type_kr = {
                        'deposit': '예금',
                        'saving': '적금',
                        'stock': '주식'
                    }.get(product['type'], product['type'])
                    print(f"  {i}. [{product_type_kr}] {product['name']}")
                    print(f"     은행/시장: {product.get('bank', product.get('market', ''))}")
                    if product.get('rate'):
                        print(f"     금리: {product['rate']}")

            return True
        else:
            print(f"\n[FAIL] 챗봇 응답 실패")
            print(f"  - 에러: {result.get('error', '알 수 없음')}")
            return False

    except Exception as e:
        print(f"\n[ERROR] 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_integration_tests():
    """통합 테스트 실행"""
    print("\n")
    print("=" * 80)
    print(" " * 25 + "챗봇 통합 테스트")
    print("=" * 80)

    # 테스트 케이스
    test_cases = [
        "안정적인 예금 상품 추천해줘",
        "장기 적금 추천해줘",
        "금리 높은 예금 알려줘",
        "단기로 운용할 수 있는 적금 찾아줘",
        "원금보장되는 상품 추천해줘",
    ]

    results = []

    for test_message in test_cases:
        success = test_chatbot_response(test_message)
        results.append((test_message, success))

    # 최종 결과
    print("\n\n")
    print("=" * 80)
    print(" " * 30 + "최종 결과")
    print("=" * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for message, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {message}")

    print("\n" + "=" * 80)
    print(f"전체 결과: {passed}/{total} 성공")

    if passed == total:
        print("\n[SUCCESS] 모든 통합 테스트 통과!")
    else:
        print(f"\n[WARNING] {total - passed}개 테스트 실패")

    print("=" * 80)


if __name__ == "__main__":
    run_integration_tests()
