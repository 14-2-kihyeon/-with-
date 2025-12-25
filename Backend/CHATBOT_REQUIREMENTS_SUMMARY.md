# 챗봇 3가지 요구사항 구현 완료

## 요구사항

1. **"(제공 데이터 내 **)" 문구 제거**: 챗봇이 사용하는 내부 문구를 사용자 친화적으로 변경
2. **가독성 개선**: 응답의 포맷팅을 개선하여 더 읽기 쉽게 만들기
3. **특정 상품/종목 질문 시 해당 항목만 응답**: 사용자가 특정 상품이나 종목을 물어보면 그것에 대해서만 답변하고, 사용자 프로필과의 적합성도 평가

## 구현 내용

### 1. 내부 문구 제거 (services.py:1179-1217)

**변경 사항**:
- 금지 문구 목록에 "제공 데이터 내", "제공된 데이터 내" 등 추가
- 괄호 안의 "(제공 데이터 내 **)" 패턴을 정규식으로 제거
- 중복 공백 정리 로직 개선 (줄바꿈은 유지하면서 공백만 정리)

**코드**:
```python
forbidden_phrases = [
    "내 DB기준", "내 DB 기준", "DB기준", "DB 기준",
    "제공 데이터 내", "제공된 데이터 내",  # 추가
    # ...
]

# 괄호 안의 "제공 데이터" 문구 제거
cleaned_response = re.sub(r'\(제공\s*데이터[^)]*\)', '', cleaned_response)
cleaned_response = re.sub(r'\(제공된\s*데이터[^)]*\)', '', cleaned_response)

# 중복 공백만 정리 (줄바꿈은 유지)
cleaned_response = re.sub(r'  +', ' ', cleaned_response)
```

### 2. 가독성 개선 (services.py:1063-1162)

**변경 사항**:
- 섹션 헤더 앞뒤에 빈 줄 자동 추가
- 불릿 포인트와 숫자 목록 인식 및 정리
- 연속된 빈 줄 제거 (최대 1개까지만 허용)
- 줄 수 제한을 15줄로 확대 (이전: 7줄)
- 길이 제한 1200자 유지
- 중요한 정보 우선 유지 (헤더, 핵심 내용)

**주요 로직**:
```python
# 섹션 헤더 처리
if stripped.startswith(('===', '##', '**')):
    if formatted_lines and formatted_lines[-1]:
        formatted_lines.append('')  # 헤더 전 빈 줄
    formatted_lines.append(stripped)
    formatted_lines.append('')  # 헤더 후 빈 줄

# 연속된 빈 줄 제거
cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

# 최대 15줄 제한
if len(non_empty_lines) > 15:
    # 중요한 정보 우선 유지 (헤더 + 최대 12개 컨텐츠)
```

### 3. 특정 상품/종목 질문 처리 (services.py:289-333, 679-722)

**변경 사항**:

#### 3.1 특정 상품명 감지 (analyze_user_question)
- 사용자 메시지에서 예금/적금 상품명을 DB와 대조하여 감지
- `specific_product_name` 필드에 저장

```python
# 예금 상품명 검사
all_deposits = DepositProducts.objects.all()
for product in all_deposits:
    if product.fin_prdt_nm and product.fin_prdt_nm in user_message:
        result['specific_product_name'] = product.fin_prdt_nm
        result['is_specific_query'] = True
        break
```

#### 3.2 특정 종목/상품 전용 시스템 프롬프트
- 특정 종목이 언급된 경우, 해당 종목에 대해서만 설명하도록 지시
- 사용자 프로필(위험 성향, 나이, 투자 기간 등)과의 적합성 평가 요구
- 다른 상품/종목 추천 금지

**주식 질문 (STOCK intent)**:
```python
if question_analysis and question_analysis.get('stock_names'):
    specific_stock_instruction = f"""
⚠️⚠️⚠️ 최우선 지침 ⚠️⚠️⚠️
사용자가 "{stock_list}" 종목에 대해 질문했습니다.
- 이 종목에 대해서만 설명하세요.
- **절대로** 다른 종목을 추천하거나 언급하지 마세요.
- 이 종목이 사용자의 프로필(위험 성향, 나이 등)에 적합한지 평가하세요.
- 위험 성향이 안정형인데 고위험 종목이라면 명확히 경고하세요.
"""
```

**금융상품 질문 (PRODUCT intent)**:
```python
if question_analysis and question_analysis.get('specific_product_name'):
    specific_product_instruction = f"""
⚠️⚠️⚠️ 최우선 지침 ⚠️⚠️⚠️
사용자가 "{product_name}" 상품에 대해 질문했습니다.
- 이 상품에 대해서만 설명하세요.
- **절대로** 다른 상품을 추천하거나 언급하지 마세요.
- 이 상품이 사용자의 프로필(투자 기간, 목표)에 적합한지 평가하세요.
- 적합하지 않다면 그 이유를 설명하되, 다른 상품을 추천하지 마세요.
"""
```

## 추가 수정 사항

### GMS API 토큰 증가
- **이전**: `max_completion_tokens`: 3000
- **변경**: `max_completion_tokens`: 5000
- **이유**: gpt-5-mini 모델이 internal reasoning에 많은 토큰을 사용하므로, 실제 출력을 위해 더 많은 토큰 필요

```python
payload = {
    "model": "gpt-5-mini",
    "messages": messages,
    "max_completion_tokens": 5000,  # 증가
}
```

### build_system_prompt 함수 시그니처 변경
- `question_analysis` 파라미터 추가
- 특정 상품/종목 정보를 프롬프트 생성 시 활용

```python
def build_system_prompt(self, user_profile, products, stocks,
                       specific_data="", fresh_news="",
                       intent="GENERAL", mode="SERVICE",
                       question_analysis=None):  # 추가
```

## 테스트 결과

**요구사항 1 검증**:
- ✅ "(제공 데이터 내)" 문구가 응답에서 제거됨
- ✅ 내부 DB 관련 문구 필터링 작동

**요구사항 2 검증**:
- ✅ 응답 길이: 평균 800-1200자로 적절하게 제한
- ✅ 줄 수: 최대 15줄로 가독성 향상
- ✅ 섹션 헤더 및 불릿 포인트 포맷팅 작동

**요구사항 3 검증**:
- ✅ 특정 종목 질문 시 해당 종목만 설명
- ✅ 사용자 프로필과의 적합성 평가 포함
- ✅ 다른 상품 추천 방지

## 파일 변경 사항

**수정된 파일**:
- `chatbot/services.py`
  - `analyze_user_question()`: 특정 상품명 감지 로직 추가
  - `build_system_prompt()`: question_analysis 파라미터 추가, 특정 상품/종목 지침 추가
  - `format_response_by_mode()`: 가독성 개선 로직 구현
  - `post_process_response()`: 내부 문구 제거 로직 강화
  - `chat()`: max_completion_tokens 5000으로 증가, question_analysis 전달

**테스트 파일 생성**:
- `test_requirements.py`: 3가지 요구사항 검증 스크립트
- `test_simple_response.py`: 간단한 응답 테스트

## 향후 개선 사항

1. **응답 품질 모니터링**: 실제 사용자 피드백을 수집하여 포맷팅 규칙 개선
2. **상품명 매칭 정확도**: 유사 상품명 처리를 위한 fuzzy matching 고려
3. **프로필 적합성 평가 기준**: 더 세밀한 적합성 평가 기준 정의

## 결론

3가지 요구사항이 모두 성공적으로 구현되었습니다:
1. ✅ 내부 문구 제거
2. ✅ 가독성 개선
3. ✅ 특정 상품/종목 전용 응답 + 프로필 적합성 평가

챗봇은 이제 더 사용자 친화적이고 읽기 쉬운 응답을 제공하며, 특정 상품이나 종목에 대한 질문에 정확하게 답변합니다.
