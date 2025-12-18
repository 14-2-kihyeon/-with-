<!-- src/views/auth/InvestmentSurveyView.vue -->
<template>
  <div class="survey-container">
    <div class="survey-header">
      <h1>투자 성향 분석</h1>
      <p class="survey-description">
        총 10개의 질문에 답변하시면 고객님의 투자 성향을 분석하여<br />
        맞춤형 금융 상품을 추천해드립니다.
      </p>
    </div>

    <!-- 진행 상태 바 -->
    <div class="progress-bar">
      <div 
        class="progress-fill" 
        :style="{ width: progressPercentage + '%' }"
      ></div>
      <span class="progress-text">{{ currentStep + 1 }} / {{ totalSteps }}</span>
    </div>

    <!-- 로딩 -->
    <div v-if="loading" class="loading">
      <p>질문을 불러오는 중...</p>
    </div>

    <!-- 설문 질문 -->
    <div v-else-if="!showResult" class="survey-content">
      <!-- 기본 정보 입력 (첫 단계) -->
      <div v-if="currentStep === 0" class="basic-info-step">
        <h2>기본 정보 입력</h2>
        <p class="step-description">보다 정확한 추천을 위해 기본 정보를 입력해주세요.</p>
        
        <div class="form-group">
          <label>나이</label>
          <input 
            v-model.number="basicInfo.age" 
            type="number" 
            placeholder="예: 30"
            min="1"
            max="100"
          />
        </div>

        <div class="form-group">
          <label>연 소득 (만원)</label>
          <input 
            v-model.number="basicInfo.income" 
            type="number" 
            placeholder="예: 5000"
            min="0"
          />
        </div>

        <div class="form-group">
          <label>현재 저축액 (만원)</label>
          <input 
            v-model.number="basicInfo.savings" 
            type="number" 
            placeholder="예: 10000"
            min="0"
          />
        </div>

        <div class="form-group">
          <label>투자 목표</label>
          <select v-model="basicInfo.investment_goal">
            <option value="">선택하세요</option>
            <option value="비상금">비상금 마련</option>
            <option value="주택구매">주택 구매</option>
            <option value="결혼자금">결혼 자금</option>
            <option value="자녀교육">자녀 교육비</option>
            <option value="노후준비">노후 준비</option>
            <option value="기타">기타</option>
          </select>
        </div>

        <div class="form-group">
          <label>투자 가능 기간 (개월)</label>
          <input 
            v-model.number="basicInfo.investment_period" 
            type="number" 
            placeholder="예: 36"
            min="1"
          />
        </div>
      </div>

      <!-- 설문 질문 (1~10번) -->
      <div v-else class="question-step">
        <div class="question-header">
          <span class="question-category">{{ currentQuestion.category_display }}</span>
          <h2 class="question-text">{{ currentQuestion.question_text }}</h2>
        </div>

        <div class="choices">
          <button
            v-for="choice in currentQuestion.choices"
            :key="choice.id"
            class="choice-button"
            :class="{ selected: responses[currentStep - 1]?.choice_id === choice.id }"
            @click="selectChoice(choice)"
          >
            <span class="choice-number">{{ choice.order }}</span>
            <span class="choice-text">{{ choice.choice_text }}</span>
            <span v-if="responses[currentStep - 1]?.choice_id === choice.id" class="check-icon">✓</span>
          </button>
        </div>
      </div>

      <!-- 네비게이션 버튼 -->
      <div class="survey-navigation">
        <button 
          class="btn-secondary" 
          @click="prevStep" 
          :disabled="currentStep === 0"
        >
          이전
        </button>
        
        <button 
          class="btn-primary" 
          @click="nextStep"
          :disabled="!canProceed"
        >
          {{ isLastStep ? '결과 확인' : '다음' }}
        </button>
      </div>
    </div>

    <!-- 결과 화면 -->
    <div v-if="showResult" class="result-container">
      <div class="result-header">
        <div class="result-icon" :class="'icon-' + result.risk_type">
          {{ getRiskIcon(result.risk_type) }}
        </div>
        <h2>{{ result.risk_type_name }}</h2>
        <p class="result-score">종합 점수: {{ result.risk_score }}점</p>
      </div>

      <div class="result-description">
        <h3>투자 성향 설명</h3>
        <p>{{ result.description }}</p>
      </div>

      <div class="result-characteristics">
        <h3>주요 특징</h3>
        <ul>
          <li v-for="(char, index) in result.characteristics" :key="index">
            {{ char }}
          </li>
        </ul>
      </div>

      <div class="result-recommendation">
        <h3>추천 상품 유형</h3>
        <p>{{ result.recommended_products_guide }}</p>
      </div>

      <div class="result-actions">
        <button class="btn-primary" @click="goToRecommendations">
          맞춤 상품 추천 보기
        </button>
        <button class="btn-secondary" @click="retakeSurvey">
          다시 검사하기
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import api from "@/api/axios"

const router = useRouter()

// 상태
const loading = ref(false)
const questions = ref([])
const currentStep = ref(0)  // 0: 기본정보, 1~10: 설문
const responses = ref([])
const showResult = ref(false)
const result = ref(null)

// 기본 정보
const basicInfo = ref({
  age: null,
  income: null,
  savings: null,
  investment_goal: "",
  investment_period: null,
})

// Computed
const totalSteps = computed(() => questions.value.length + 1)  // 기본정보 + 설문
const progressPercentage = computed(() => ((currentStep.value + 1) / totalSteps.value) * 100)
const currentQuestion = computed(() => questions.value[currentStep.value - 1])
const isLastStep = computed(() => currentStep.value === totalSteps.value - 1)

const canProceed = computed(() => {
  if (currentStep.value === 0) {
    // 기본정보: 모든 필드 입력 확인
    return (
      basicInfo.value.age &&
      basicInfo.value.income !== null &&
      basicInfo.value.savings !== null &&
      basicInfo.value.investment_goal &&
      basicInfo.value.investment_period
    )
  } else {
    // 설문: 현재 질문에 답변했는지 확인
    return responses.value[currentStep.value - 1]?.choice_id
  }
})

// Methods
const fetchQuestions = async () => {
  loading.value = true
  try {
    const res = await api.get("/accounts/survey/questions/")
    questions.value = res.data
  } catch (error) {
    console.error("질문 로딩 실패:", error)
    alert("질문을 불러오는데 실패했습니다.")
  } finally {
    loading.value = false
  }
}

const selectChoice = (choice) => {
  const questionId = currentQuestion.value.id
  
  // 기존 응답 업데이트 또는 새로 추가
  const existingIndex = responses.value.findIndex(
    (r) => r.question_id === questionId
  )
  
  if (existingIndex !== -1) {
    responses.value[existingIndex] = {
      question_id: questionId,
      choice_id: choice.id,
    }
  } else {
    responses.value.push({
      question_id: questionId,
      choice_id: choice.id,
    })
  }
}

const nextStep = async () => {
  if (isLastStep.value) {
    // 마지막 질문 → 제출
    await submitSurvey()
  } else {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const submitSurvey = async () => {
  loading.value = true
  try {
    const res = await api.post("/accounts/survey/submit/", {
      responses: responses.value,
      ...basicInfo.value,
    })
    
    result.value = res.data
    showResult.value = true
  } catch (error) {
    console.error("제출 실패:", error)
    alert(error.response?.data?.detail || "제출에 실패했습니다.")
  } finally {
    loading.value = false
  }
}

const goToRecommendations = () => {
  router.push({ name: "recommendations" })
}

const retakeSurvey = () => {
  currentStep.value = 0
  responses.value = []
  showResult.value = false
  result.value = null
  basicInfo.value = {
    age: null,
    income: null,
    savings: null,
    investment_goal: "",
    investment_period: null,
  }
}

const getRiskIcon = (riskType) => {
  const icons = {
    very_conservative: "🛡️",
    conservative: "🏦",
    moderate: "⚖️",
    aggressive: "📈",
    very_aggressive: "🚀",
  }
  return icons[riskType] || "📊"
}

onMounted(() => {
  fetchQuestions()
})
</script>

<style scoped>
.survey-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 20px;
}

.survey-header {
  text-align: center;
  margin-bottom: 40px;
}

.survey-header h1 {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 16px;
  color: #1a1a1a;
}

.survey-description {
  font-size: 16px;
  color: #666;
  line-height: 1.6;
}

/* 진행 상태 바 */
.progress-bar {
  position: relative;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  margin-bottom: 40px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  top: 16px;
  right: 0;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

/* 기본 정보 입력 */
.basic-info-step h2 {
  font-size: 24px;
  margin-bottom: 12px;
  color: #1a1a1a;
}

.step-description {
  font-size: 14px;
  color: #666;
  margin-bottom: 32px;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #4f46e5;
}

/* 질문 */
.question-step {
  margin-bottom: 40px;
}

.question-header {
  margin-bottom: 32px;
}

.question-category {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  color: #7c3aed;
  background: #f3f0ff;
  padding: 4px 12px;
  border-radius: 12px;
  margin-bottom: 16px;
}

.question-text {
  font-size: 22px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
}

/* 선택지 */
.choices {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.choice-button {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.choice-button:hover {
  border-color: #4f46e5;
  background: #f9fafb;
}

.choice-button.selected {
  border-color: #4f46e5;
  background: #eef2ff;
}

.choice-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #f3f4f6;
  border-radius: 50%;
  font-weight: 600;
  color: #6b7280;
  flex-shrink: 0;
}

.choice-button.selected .choice-number {
  background: #4f46e5;
  color: white;
}

.choice-text {
  flex: 1;
  font-size: 15px;
  color: #374151;
  line-height: 1.5;
}

.check-icon {
  font-size: 20px;
  color: #4f46e5;
}

/* 네비게이션 */
.survey-navigation {
  display: flex;
  gap: 16px;
  justify-content: space-between;
  margin-top: 40px;
}

.btn-primary,
.btn-secondary {
  flex: 1;
  padding: 14px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #4f46e5;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #4338ca;
}

.btn-secondary {
  background: white;
  color: #4f46e5;
  border: 2px solid #4f46e5;
}

.btn-secondary:hover:not(:disabled) {
  background: #eef2ff;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 결과 화면 */
.result-container {
  text-align: center;
}

.result-header {
  margin-bottom: 40px;
  padding: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
}

.result-icon {
  font-size: 80px;
  margin-bottom: 16px;
}

.result-header h2 {
  font-size: 32px;
  margin-bottom: 12px;
}

.result-score {
  font-size: 18px;
  opacity: 0.9;
}

.result-description,
.result-characteristics,
.result-recommendation {
  text-align: left;
  margin-bottom: 32px;
  padding: 24px;
  background: #f9fafb;
  border-radius: 12px;
}

.result-description h3,
.result-characteristics h3,
.result-recommendation h3 {
  font-size: 20px;
  margin-bottom: 16px;
  color: #1a1a1a;
}

.result-description p,
.result-recommendation p {
  font-size: 16px;
  color: #4b5563;
  line-height: 1.6;
}

.result-characteristics ul {
  list-style: none;
  padding: 0;
}

.result-characteristics li {
  padding: 12px 0;
  border-bottom: 1px solid #e5e7eb;
  color: #4b5563;
}

.result-characteristics li:last-child {
  border-bottom: none;
}

.result-characteristics li::before {
  content: "✓";
  color: #10b981;
  font-weight: bold;
  margin-right: 12px;
}

.result-actions {
  display: flex;
  gap: 16px;
  margin-top: 40px;
}

.loading {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}
</style>