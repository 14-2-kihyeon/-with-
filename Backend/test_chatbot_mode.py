"""
챗봇 모드 분류 시스템 테스트 스크립트
Django 환경에서 실행: python manage.py shell < test_chatbot_mode.py
"""

import os
import django

# Django 설정 (manage.py 없이 실행 시)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from chatbot.mode_classifier import classify_chat_mode
from chatbot.services import ChatbotService
from django.contrib.auth import get_user_model

print("=" * 80)
print("Finflow AI 챗봇 모드 분류 시스템 테스트")
print("=" * 80)

# ===== 1단계: 모드 분류기 단독 테스트 =====
print("\n[1단계] 모드 분류기 테스트")
print("-" * 80)

test_cases = [
    # CHAT 모드 예상
    ("안녕", "CHAT"),
    ("고마워", "CHAT"),
    ("ㅋㅋㅋ", "CHAT"),
    ("좋아", "CHAT"),
    ("오늘 날씨 어때?", "CHAT"),
    ("넌 누구야?", "CHAT"),
    ("하이", "CHAT"),
    ("응", "CHAT"),

    # SERVICE 모드 예상
    ("삼전 어때?", "SERVICE"),
    ("삼성전자 주가 알려줘", "SERVICE"),
    ("예금 추천해줘", "SERVICE"),
    ("금리 좋은 적금", "SERVICE"),
    ("북마크 어디서 봐?", "SERVICE"),
    ("나중에 볼 영상 목록", "SERVICE"),
    ("005930 분석", "SERVICE"),
    ("마이페이지 조회", "SERVICE"),
    ("주식 추천", "SERVICE"),
    ("뉴스 알려줘", "SERVICE"),
]

correct = 0
total = len(test_cases)

for query, expected in test_cases:
    actual = classify_chat_mode(query)
    status = "✅" if actual == expected else "❌"
    if actual == expected:
        correct += 1
    print(f"{status} '{query:30s}' → {actual:10s} (기대: {expected})")

print("-" * 80)
print(f"정확도: {correct}/{total} ({correct/total*100:.1f}%)")

# ===== 2단계: 실제 챗봇 응답 테스트 =====
print("\n[2단계] 실제 챗봇 응답 테스트")
print("-" * 80)

User = get_user_model()
try:
    user = User.objects.first()
    if not user:
        print("⚠️ 테스트용 사용자가 없습니다. 사용자를 먼저 생성하세요.")
    else:
        chatbot = ChatbotService(user)

        # CHAT 모드 테스트 케이스
        chat_test_cases = [
            "안녕",
            "고마워",
            "ㅋㅋㅋ",
        ]

        print("\n[CHAT 모드 응답 테스트]")
        for query in chat_test_cases:
            print(f"\n입력: '{query}'")
            try:
                result = chatbot.chat(query)
                response = result['response']
                products = result.get('recommended_products')

                print(f"응답 길이: {len(response)}자")
                print(f"응답 줄 수: {len([l for l in response.split('\\n') if l.strip()])}줄")
                print(f"추천 상품: {products}")
                print(f"응답 내용: {response[:200]}..." if len(response) > 200 else f"응답 내용: {response}")

                # 검증
                if len(response) > 300:
                    print("⚠️ 경고: CHAT 모드 응답이 300자를 초과했습니다!")
                if products is not None:
                    print("⚠️ 경고: CHAT 모드에서 상품 추천이 발생했습니다!")
                if any(kw in response for kw in ['예금', '적금', '주식', '금리', '수익률']):
                    print("⚠️ 경고: CHAT 모드에서 금융 상품 정보가 포함되었습니다!")

            except Exception as e:
                print(f"❌ 오류 발생: {str(e)}")

        # SERVICE 모드 테스트 케이스
        service_test_cases = [
            "삼전 어때?",
            "예금 추천해줘",
        ]

        print("\n\n[SERVICE 모드 응답 테스트]")
        for query in service_test_cases:
            print(f"\n입력: '{query}'")
            try:
                result = chatbot.chat(query)
                response = result['response']
                products = result.get('recommended_products')

                print(f"응답 길이: {len(response)}자")
                print(f"응답 줄 수: {len([l for l in response.split('\\n') if l.strip()])}줄")
                print(f"추천 상품 수: {len(products) if products else 0}개")
                print(f"응답 내용: {response[:300]}..." if len(response) > 300 else f"응답 내용: {response}")

                # 검증
                if len(response) > 1200:
                    print("⚠️ 경고: SERVICE 모드 응답이 1200자를 초과했습니다!")
                lines = [l for l in response.split('\\n') if l.strip()]
                if len(lines) > 7:
                    print(f"⚠️ 경고: SERVICE 모드 응답이 7줄을 초과했습니다! (현재: {len(lines)}줄)")

            except Exception as e:
                print(f"❌ 오류 발생: {str(e)}")
                import traceback
                traceback.print_exc()

except Exception as e:
    print(f"❌ 테스트 실행 오류: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("테스트 완료!")
print("=" * 80)
