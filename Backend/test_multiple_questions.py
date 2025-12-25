"""
여러 질문 테스트
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

# 테스트 질문들
questions = [
    "안정적인 예금 상품 추천해줘",
    "장기 적금 추천해줘",
    "금리 높은 예금 알려줘",
]

results = []

for i, question in enumerate(questions, 1):
    print(f"\n{'=' * 80}")
    print(f"테스트 {i}/{len(questions)}: {question}")
    print("=" * 80)

    try:
        # 의도 분석
        analysis = chatbot.analyze_user_question(question)
        intent = analysis['intent']
        print(f"의도: {intent}")

        # 응답 생성
        result = chatbot.chat(question)

        if result['success']:
            print("[PASS] 응답 성공")
            print(f"  - 응답 길이: {len(result['response'])}자")

            if result.get('recommended_products'):
                print(f"  - 추천 상품: {len(result['recommended_products'])}개")
                for p in result['recommended_products'][:2]:
                    print(f"    * {p['name']}")

            results.append((question, True, intent))
        else:
            print(f"[FAIL] 응답 실패: {result.get('error')}")
            results.append((question, False, intent))

    except Exception as e:
        print(f"[ERROR] 예외: {e}")
        results.append((question, False, "ERROR"))

# 결과 요약
print(f"\n\n{'=' * 80}")
print("최종 결과")
print("=" * 80)

passed = sum(1 for _, success, _ in results if success)
total = len(results)

for q, success, intent in results:
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} {q} (의도: {intent})")

print(f"\n전체: {passed}/{total} 성공")

if passed == total:
    print("[SUCCESS] 모든 테스트 통과!")
else:
    print(f"[WARNING] {total - passed}개 실패")
