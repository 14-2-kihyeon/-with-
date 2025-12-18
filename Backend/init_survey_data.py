"""
설문 데이터 초기화 스크립트
Backend 폴더에서 실행: python init_survey_data.py
"""

import os
import sys
import django

# ✅ Django 설정 로드 (이게 없어서 에러 발생!)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Finflow.settings')
django.setup()

from accounts.models import SurveyQuestion, SurveyChoice, SURVEY_DATA

# 1. 기존 데이터 삭제
print("기존 데이터 삭제 중...")
SurveyQuestion.objects.all().delete()
print("삭제 완료!")

# 2. 새 데이터 생성
print("\n새 데이터 생성 중...\n")

for q_data in SURVEY_DATA:
    # 질문 생성
    question = SurveyQuestion.objects.create(
        category=q_data['category'],
        question_text=q_data['question_text'],
        order=q_data['order']
    )
    
    print(f"질문 {question.order} 생성: {question.question_text[:40]}...")
    
    # 선택지 생성 (이 부분이 중요!)
    for idx, choice_data in enumerate(q_data['choices'], 1):
        choice = SurveyChoice.objects.create(
            question=question,
            choice_text=choice_data['choice_text'],
            score=choice_data['score'],
            order=idx,
        )
        print(f"  ✓ 선택지 {idx}: {choice.choice_text[:40]}...")

# 3. 결과 확인
print("\n" + "="*50)
print("초기화 완료!")
print("="*50)
print(f"총 질문: {SurveyQuestion.objects.count()}개")
print(f"총 선택지: {SurveyChoice.objects.count()}개")

# 첫 번째 질문의 선택지 확인
q = SurveyQuestion.objects.first()
print(f"\n첫 번째 질문: {q.question_text}")
print(f"선택지 개수: {q.choices.count()}개")

if q.choices.count() > 0:
    print("\n선택지 목록:")
    for choice in q.choices.all():
        print(f"  {choice.order}. {choice.choice_text} (점수: {choice.score})")
else:
    print("⚠️ 선택지가 없습니다! 초기화에 문제가 있습니다.")