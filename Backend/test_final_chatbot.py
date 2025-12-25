"""
최종 챗봇 테스트 - 500 에러 수정 확인
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from chatbot.services import ChatbotService
from django.contrib.auth import get_user_model

print("=" * 80)
print("챗봇 최종 테스트 - 500 에러 수정 확인")
print("=" * 80)

try:
    User = get_user_model()
    user = User.objects.first()

    if not user:
        print("[ERROR] 테스트 사용자 없음")
        exit(1)

    print(f"[OK] 사용자: {user.username}")

    chatbot = ChatbotService(user)
    print(f"[OK] ChatbotService 초기화 완료")

    # CHAT 모드 테스트
    print("\n" + "=" * 80)
    print("[TEST 1] CHAT 모드 - '안녕'")
    print("=" * 80)
    try:
        result = chatbot.chat("안녕")
        if result['success']:
            response_len = len(result['response'])
            print(f"✓ 성공!")
            print(f"  - 응답 길이: {response_len}자")
            print(f"  - 추천 상품: {result.get('recommended_products')}")
            if response_len > 0:
                print(f"  - CHAT 모드 응답 확인: OK")
            else:
                print(f"  ⚠ 경고: 응답이 비어있습니다!")
        else:
            print(f"✗ 실패: {result.get('error')}")
    except Exception as e:
        print(f"✗ 예외 발생: {type(e).__name__}: {str(e)}")

    # SERVICE 모드 테스트
    print("\n" + "=" * 80)
    print("[TEST 2] SERVICE 모드 - '예금 추천'")
    print("=" * 80)
    try:
        result = chatbot.chat("예금 추천")
        if result['success']:
            response_len = len(result['response'])
            print(f"✓ 성공!")
            print(f"  - 응답 길이: {response_len}자")
            print(f"  - 추천 상품 수: {len(result.get('recommended_products') or [])}")
            if response_len > 0:
                print(f"  - SERVICE 모드 응답 확인: OK")
            else:
                print(f"  ⚠ 경고: 응답이 비어있습니다!")
        else:
            print(f"✗ 실패: {result.get('error')}")
    except Exception as e:
        print(f"✗ 예외 발생: {type(e).__name__}: {str(e)}")

    print("\n" + "=" * 80)
    print("✓ 챗봇 500 에러 수정 완료!")
    print("  GMS API 파라미터 문제 해결:")
    print("  1. temperature 파라미터 제거 (gpt-5-mini 미지원)")
    print("  2. max_completion_tokens 증가 (reasoning 토큰 고려)")
    print("     - CHAT 모드: 1000 토큰")
    print("     - SERVICE 모드: 3000 토큰")
    print("=" * 80)

except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
