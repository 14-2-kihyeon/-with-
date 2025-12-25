"""
상품 필드 확인
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from finances.models import DepositProducts, SavingProducts

print("=" * 80)
print("예금 상품 필드 확인")
print("=" * 80)

# join_deny 값 확인
print("\njoin_deny 값들:")
for val in DepositProducts.objects.values_list('join_deny', flat=True).distinct():
    count = DepositProducts.objects.filter(join_deny=val).count()
    print(f"  {val}: {count}개 상품")

# join_member 값 확인
print("\njoin_member 값들 (샘플):")
for product in DepositProducts.objects.exclude(join_member='').exclude(join_member__isnull=True)[:10]:
    print(f"  {product.fin_prdt_nm[:30]:30s} | {product.join_member}")

# 미즈월 상품 상세 확인
print("\n미즈월 상품 상세:")
mizz = DepositProducts.objects.filter(fin_prdt_nm__contains='미즈').first()
if mizz:
    print(f"  상품명: {mizz.fin_prdt_nm}")
    print(f"  join_deny: {mizz.join_deny}")
    print(f"  join_member: {mizz.join_member}")
    print(f"  spcl_cnd: {mizz.spcl_cnd}")

# 최고 금리순 정렬 확인
print("\n최고 금리순 상위 5개:")
from finances.models import DepositOptions
from django.db.models import Max

deposits_with_rate = DepositProducts.objects.annotate(
    max_rate=Max('options__intr_rate2')
).order_by('-max_rate')[:5]

for d in deposits_with_rate:
    print(f"  {d.kor_co_nm:10s} | {d.fin_prdt_nm:30s} | 최고금리: {d.max_rate}%")

print("\n" + "=" * 80)
