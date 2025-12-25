"""
투자 성향별 가중치 적용 추천 테스트
- 동일한 조건에서 안정형/중립형/공격형 사용자의 추천 상품 차이 확인
"""
import os
import sys
import django

# Windows 인코딩 문제 해결
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import InvestmentProfile
from rest_framework.test import APIRequestFactory
from accounts.views import recommend_products

User = get_user_model()

# 테스트용 사용자 생성/조회
def get_or_create_test_user(username, risk_type, gender='M'):
    user, created = User.objects.get_or_create(username=username)

    # 프로필 생성 또는 업데이트
    profile, _ = InvestmentProfile.objects.get_or_create(user=user)
    profile.risk_type = risk_type
    profile.risk_score = {'timid_male': 30, 'normal_male': 60, 'speculative_male': 90}[risk_type]
    profile.gender = gender
    profile.age = 30
    profile.savings = 10000000  # 1천만원
    profile.investment_period = 12  # 12개월
    profile.investment_goal = 'stable_income'
    profile.save()

    return user

print("=" * 100)
print("투자 성향별 추천 상품 차이 테스트")
print("=" * 100)

# 3가지 투자 성향별 사용자 생성 (남성 기준)
risk_types = [
    ('timid_male', '안정형 (에겐소심남)', 'test_timid_male'),
    ('normal_male', '중립형 (보통남)', 'test_normal_male'),
    ('speculative_male', '공격형 (테토투기남)', 'test_speculative_male'),
]

factory = APIRequestFactory()
results = {}

for risk_type, risk_name, username in risk_types:
    print(f"\n{'=' * 100}")
    print(f"[{risk_name}] 사용자 테스트")
    print("=" * 100)

    # 사용자 생성
    user = get_or_create_test_user(username, risk_type)

    # API 요청 생성 (force_authenticate 사용)
    request = factory.get('/api/v1/accounts/recommend/')
    # force_authenticate를 사용하여 인증 우회
    from rest_framework.test import force_authenticate
    force_authenticate(request, user=user)

    try:
        # 추천 API 호출
        response = recommend_products(request)
        data = response.data

        print(f"\n[DEBUG] Response keys: {list(data.keys())}")
        print(f"[DEBUG] Recommendations count: {len(data.get('recommendations', []))}")

        if 'detail' in data:
            print(f"[DEBUG] Error detail: {data['detail']}")

        if data.get('recommendations'):
            recommendations = data['recommendations']
            results[risk_type] = recommendations

            print(f"\n✅ 추천 상품 수: {len(recommendations)}개")
            print(f"투자 성향: {data['profile']['risk_type_name']} (점수: {data['profile']['risk_score']})")

            print("\n상위 5개 추천 상품:")
            for i, rec in enumerate(recommendations[:5], 1):
                product = rec['product']
                option = rec['option']
                score = rec.get('match_score', 0)

                # 가중치 점수는 risk_adjusted_score 필드에 있음
                risk_score = rec.get('risk_adjusted_score', 0)

                print(f"\n{i}. [{rec.get('type', 'N/A').upper()}] {product['fin_prdt_nm']}")
                print(f"   은행: {product['kor_co_nm']}")
                print(f"   기본금리: {option['intr_rate']:.2f}%")
                print(f"   최고금리: {option['intr_rate2']:.2f}%")
                print(f"   가입기간: {option.get('save_trm', 'N/A')}개월")
                print(f"   ⭐ 가중치 점수: {risk_score:.2f}점")

                # 우대조건 미리보기
                spcl_cnd = product.get('spcl_cnd', '')
                if spcl_cnd and len(spcl_cnd) > 100:
                    print(f"   우대조건: {spcl_cnd[:100]}...")
                elif spcl_cnd:
                    print(f"   우대조건: {spcl_cnd}")
        else:
            print(f"\n❌ 추천 상품 없음")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

# 비교 분석
print(f"\n\n{'=' * 100}")
print("투자 성향별 추천 차이 비교")
print("=" * 100)

if len(results) == 3:
    print("\n동일 상품에 대한 가중치 점수 비교:")
    print("-" * 100)

    # 안정형 상위 3개 상품을 기준으로 비교
    conservative_recs = results['timid_male'][:3]

    for i, cons_rec in enumerate(conservative_recs, 1):
        product_name = cons_rec['product']['fin_prdt_nm']
        product_code = cons_rec['product']['fin_prdt_cd']
        cons_score = cons_rec.get('risk_adjusted_score', 0)

        print(f"\n{i}. {product_name}")
        print(f"   상품코드: {product_code}")

        # 중립형에서 같은 상품 찾기
        moderate_rec = next((r for r in results['normal_male'] if r['product']['fin_prdt_cd'] == product_code), None)
        moderate_score = moderate_rec.get('risk_adjusted_score', 0) if moderate_rec else None

        # 공격형에서 같은 상품 찾기
        aggressive_rec = next((r for r in results['speculative_male'] if r['product']['fin_prdt_cd'] == product_code), None)
        aggressive_score = aggressive_rec.get('risk_adjusted_score', 0) if aggressive_rec else None

        print(f"   안정형 점수: {cons_score:.2f}점")
        if moderate_score is not None:
            print(f"   중립형 점수: {moderate_score:.2f}점 (차이: {moderate_score - cons_score:+.2f})")
        else:
            print(f"   중립형 점수: N/A (추천 목록에 없음)")

        if aggressive_score is not None:
            print(f"   공격형 점수: {aggressive_score:.2f}점 (차이: {aggressive_score - cons_score:+.2f})")
        else:
            print(f"   공격형 점수: N/A (추천 목록에 없음)")

# 순위 변동 분석
print(f"\n\n{'=' * 100}")
print("투자 성향별 상위 5개 상품 비교")
print("=" * 100)

if len(results) == 3:
    for risk_type, risk_name, _ in risk_types:
        recs = results[risk_type][:5]
        print(f"\n[{risk_name}] 상위 5개:")
        for i, rec in enumerate(recs, 1):
            score = rec.get('risk_adjusted_score', 0)
            product_name = rec['product']['fin_prdt_nm'][:30]
            print(f"  {i}. {product_name:30} (점수: {score:.2f})")

# 최종 요약
print(f"\n\n{'=' * 100}")
print("테스트 결과 요약")
print("=" * 100)

success_count = len(results)
print(f"\n✅ 성공한 테스트: {success_count}/3")

if success_count == 3:
    print("\n예상 결과:")
    print("  - 안정형: 기본금리 높은 상품, 우대조건 단순한 상품이 상위 랭크")
    print("  - 중립형: 기본금리와 최고금리의 균형을 고려한 추천")
    print("  - 공격형: 최고금리 높은 상품이 상위 랭크 (우대조건 복잡해도 OK)")
    print("\n각 투자 성향별로 다른 가중치 점수가 적용되었는지 확인하세요!")
    print("\n[SUCCESS] 모든 테스트 통과!")
else:
    print("\n[WARNING] 일부 테스트 실패")
