"""
챗봇 맞춤 추천 빠른 테스트
"""
import os
import sys
import django

sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import InvestmentProfile
from chatbot.services import ChatbotService

User = get_user_model()

# 테스트 사용자
user = User.objects.first()
if not user:
    print("❌ 사용자가 없습니다")
    exit(1)

print("=" * 80)
print("챗봇 맞춤 추천 통합 테스트")
print("=" * 80)

# 프로필 확인
try:
    profile = user.investment_profile
    print(f"\n사용자: {user.username}")
    print(f"투자 성향: {profile.risk_type}")
    print(f"나이: {profile.age}세")
    print(f"투자 기간: {profile.investment_period}개월")
except:
    print("❌ 프로필이 없습니다")
    exit(1)

# 챗봇 초기화
chatbot = ChatbotService(user)

# 맞춤 추천 컨텍스트 테스트
print(f"\n{'=' * 80}")
print("1. 맞춤 추천 컨텍스트 생성 테스트")
print("=" * 80)

try:
    result = chatbot.get_personalized_products_context(top_k=5)

    print(f"\n추천 개수: {result['recommendation_count']}개")
    print(f"\n컨텍스트:\n{result['rag_context']}")

    if result['recommendation_count'] > 0:
        print("\n✅ 맞춤 추천 컨텍스트 생성 성공!")
    else:
        print("\n❌ 추천 상품이 없습니다")

except Exception as e:
    print(f"\n❌ 오류: {e}")
    import traceback
    traceback.print_exc()

# 챗봇 응답 테스트
print(f"\n{'=' * 80}")
print("2. 챗봇 응답 테스트")
print("=" * 80)

question = "안정적인 예금 상품 추천해줘"
print(f"\n질문: {question}")

try:
    result = chatbot.chat(question)

    if result['success']:
        print("\n✅ 응답 성공")
        print(f"\n응답 (처음 500자):")
        print(result['response'][:500])

        if result.get('recommended_products'):
            print(f"\n추천 상품: {len(result['recommended_products'])}개")
            for i, p in enumerate(result['recommended_products'][:3], 1):
                print(f"  {i}. {p['name']} ({p.get('bank', 'N/A')})")
        else:
            print("\n추천 상품: 없음")
    else:
        print(f"\n❌ 응답 실패: {result.get('error')}")

except Exception as e:
    print(f"\n❌ 오류: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'=' * 80}")
print("테스트 완료")
print("=" * 80)
