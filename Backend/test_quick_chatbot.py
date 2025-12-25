"""
빠른 챗봇 테스트 (단일 질문)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from chatbot.services import ChatbotService
from django.contrib.auth import get_user_model

User = get_user_model()

user = User.objects.first()
if not user:
    print("[ERROR] 테스트 사용자 없음")
    exit(1)

chatbot = ChatbotService(user)
user_message = "안정적인 예금 상품 추천해줘"

print("=" * 80)
print(f"질문: {user_message}")
print("=" * 80)

try:
    # 의도 분석
    print("\n[1] 의도 분석 중...")
    analysis = chatbot.analyze_user_question(user_message)
    print(f"  의도: {analysis['intent']}")

    # 응답 생성
    print("\n[2] 응답 생성 중...")
    result = chatbot.chat(user_message)

    if result['success']:
        print("\n[SUCCESS] 응답 생성 성공")
        print(f"\n응답 길이: {len(result['response'])}자")

        # 추천 상품 확인
        if result.get('recommended_products'):
            print(f"\n추천 상품 수: {len(result['recommended_products'])}개")
            for i, p in enumerate(result['recommended_products'][:3], 1):
                print(f"  {i}. {p['name']} ({p.get('bank', '')})")

        print("\n[PASS] 테스트 성공!")
    else:
        print(f"\n[FAIL] 응답 실패: {result.get('error')}")

except Exception as e:
    print(f"\n[ERROR] 예외 발생: {e}")
    import traceback
    traceback.print_exc()
