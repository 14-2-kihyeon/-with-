<!-- src/views/auth/InvestmentSurveyView.vue -->
<template>
  <div class="survey-container">
    <!-- Alert Modal -->
    <AlertModal
      v-model="showAlert"
      :icon="alertConfig.icon"
      :title="alertConfig.title"
      :message="alertConfig.message"
      :confirm-text="alertConfig.confirmText"
      @confirm="alertConfig.onConfirm"
    />

    <div class="survey-header">
      <div class="header-badge">PBTI</div>
      <h1>투자 성향 분석</h1>
      <p class="survey-description">
        10개의 질문으로 나만의 투자 성향을 찾아보세요<br />
        <span class="highlight">맞춤형 금융 상품 추천</span>까지 한 번에!
      </p>
    </div>

    <!-- 진행 상태 바 -->
    <div class="progress-section">
      <div class="progress-bar">
        <div
          class="progress-fill"
          :style="{ width: progressPercentage + '%' }"
        >
          <span class="progress-glow"></span>
        </div>
      </div>
      <div class="progress-info">
        <span class="progress-text">{{ currentStep + 1 }} / {{ totalSteps }}</span>
        <span class="progress-percent">{{ Math.round(progressPercentage) }}%</span>
      </div>
    </div>

    <!-- 로딩 -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>분석 준비 중...</p>
    </div>

    <!-- 설문 질문 -->
    <div v-else-if="!showResult" class="survey-content">
      <!-- 기본 정보 입력 (첫 단계) -->
      <div v-if="currentStep === 0" class="basic-info-step">
        <div class="step-header">
          <span class="step-number">STEP 1</span>
          <h2>기본 정보를 입력해주세요</h2>
          <p class="step-description">정확한 분석을 위한 기본 정보가 필요해요</p>
        </div>

        <!-- 성별 선택 (추가) -->
        <div class="form-group gender-group">
          <label class="required">성별</label>
          <div class="gender-options">
            <button
              type="button"
              class="gender-btn"
              :class="{ selected: basicInfo.gender === 'M' }"
              @click="basicInfo.gender = 'M'"
            >
              <span class="gender-icon">🧑🏻</span>
              <span class="gender-text">남성</span>
            </button>
            <button
              type="button"
              class="gender-btn"
              :class="{ selected: basicInfo.gender === 'F' }"
              @click="basicInfo.gender = 'F'"
            >
              <span class="gender-icon">👧🏻</span>
              <span class="gender-text">여성</span>
            </button>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="required">나이</label>
            <div class="input-wrapper">
              <input
                v-model.number="basicInfo.age"
                type="number"
                placeholder="30"
                min="1"
                max="100"
              />
              <span class="input-unit">세</span>
            </div>
          </div>

          <div class="form-group">
            <label class="required">연 소득</label>
            <div class="input-wrapper">
              <input
                v-model.number="basicInfo.income"
                type="number"
                placeholder="5000"
                min="0"
              />
              <span class="input-unit">만원</span>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label class="required">현재 저축액</label>
          <div class="input-wrapper">
            <input
              v-model.number="basicInfo.savings"
              type="number"
              placeholder="10000"
              min="0"
            />
            <span class="input-unit">만원</span>
          </div>
        </div>

        <div class="form-group">
          <label class="required">투자 목표</label>
          <select v-model="basicInfo.investment_goal" class="select-input">
            <option value="" disabled>목표를 선택하세요</option>
            <option value="비상금">💰 비상금 마련</option>
            <option value="주택구매">🏡 주택 구매</option>
            <option value="결혼자금">💒 결혼 자금</option>
            <option value="자녀교육">🎓 자녀 교육비</option>
            <option value="노후준비">🎅🏻 노후 준비</option>
            <option value="기타">🎸 기타</option>
          </select>
        </div>

        <div class="form-group">
          <label class="required">투자 가능 기간</label>
          <div class="input-wrapper">
            <input
              v-model.number="basicInfo.investment_period"
              type="number"
              placeholder="36"
              min="1"
            />
            <span class="input-unit">개월</span>
          </div>
        </div>
      </div>

      <!-- 설문 질문 (1~10번) -->
      <div v-else class="question-step">
        <div class="question-header">
          <span class="question-badge">{{ currentQuestion.category_display }}</span>
          <span class="question-number">Q{{ currentStep }}</span>
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
            <span class="choice-marker">
              <span class="choice-number">{{ choice.order }}</span>
            </span>
            <span class="choice-text">{{ choice.choice_text }}</span>
            <span v-if="responses[currentStep - 1]?.choice_id === choice.id" class="check-icon">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M7 10L9 12L13 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
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
          <span class="btn-icon">←</span>
          이전
        </button>

        <button
          class="btn-primary"
          @click="nextStep"
          :disabled="!canProceed"
        >
          {{ isLastStep ? '결과 확인' : '다음' }}
          <span class="btn-icon">{{ isLastStep ? '✓' : '→' }}</span>
        </button>
      </div>
    </div>

    <!-- 결과 동영상 팝업 -->
    <ResultVideoPopup
      v-if="result"
      :risk-type="result.risk_type"
      :show="showVideoPopup"
      @close="showVideoPopup = false"
    />

    <!-- 결과 화면 -->
    <div v-if="showResult" class="result-container">
      <div class="result-card">
        <div
          class="result-header"
          :class="'type-' + getTypeKey(result.risk_type)"
          :style="{
            backgroundImage: `url(${getCharacterImage(result.risk_type)})`
          }"
        >
          <div class="result-title">
            <!-- <span class="result-type">당신의 투자 성향</span> -->
          </div>
        </div>


        <div class="result-body">
          <div class="result-section">
            <div class="section-icon"></div>
            <h3>💡 투자 성향 설명</h3>
            <p class="section-text">{{ result.description }}</p>
          </div>

          <div class="result-section">
            <div class="section-icon"></div>
            <h3>⭐ 주요 특징</h3>
            <ul class="characteristics-list">
              <li v-for="(char, index) in result.characteristics" :key="index">
                <span class="char-icon">✓</span>
                <span class="char-text">{{ char }}</span>
              </li>
            </ul>
          </div>

          <div class="result-section recommendation-section">
            <div class="section-icon"></div>
            <h3>🎯 추천 금융 상품</h3>
            <div class="products-tags">
              <span
                v-for="(product, index) in result.recommended_products?.split(', ') || []"
                :key="index"
                class="product-tag"
              >
                {{ product }}
              </span>
            </div>
          </div>
        </div>

        <div class="result-actions">
          <button class="btn-primary btn-large" @click="goToRecommendations">
            <span class="btn-icon">🎁</span>
            맞춤 상품 추천 보기
          </button>
          <button class="btn-outline" @click="retakeSurvey">
            <span class="btn-icon">🔄</span>
            다시 검사하기
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import api from "@/api/axios"
import AlertModal from "@/components/common/AlertModal.vue"
import ResultVideoPopup from "@/components/common/ResultVideoPopup.vue"
import { useAlert } from "@/composables/useAlert"
import { useChatbot } from "@/composables/useChatbot"

// character images
import timidMale from "@/assets/character/timid_male.png"
import timidFemale from "@/assets/character/timid_female.png"
import normalMale from "@/assets/character/normal_male.png"
import normalFemale from "@/assets/character/normal_female.png"
import speculativeMale from "@/assets/character/speculative_male.png"
import speculativeFemale from "@/assets/character/speculative_female.png"

const getCharacterImage = (riskType) => {
  const map = {
    timid_male: timidMale,
    timid_female: timidFemale,
    normal_male: normalMale,
    normal_female: normalFemale,
    speculative_male: speculativeMale,
    speculative_female: speculativeFemale,
  }

  return map[riskType] || normalMale
}


const router = useRouter()

// Alert composable
const { showAlert, alertConfig, error } = useAlert()

// Chatbot composable
const { requestRefreshAvatar } = useChatbot()

// 상태
const loading = ref(false)
const questions = ref([])
const currentStep = ref(0)  // 0: 기본정보, 1~10: 설문
const responses = ref([])
const showResult = ref(false)
const result = ref(null)
const showVideoPopup = ref(false)

// 기본 정보
const basicInfo = ref({
  gender: "",  // ✅ 추가
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
    // 기본정보: 모든 필드 입력 확인 (성별 포함)
    return (
      basicInfo.value.gender &&
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
  } catch (err) {
    console.error("질문 로딩 실패:", err)
    error("질문을 불러오는데 실패했습니다.")
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
    console.log('설문 결과:', result.value)
    console.log('risk_type:', result.value.risk_type)

    showResult.value = true

    // 동영상 팝업 표시
    showVideoPopup.value = true
    console.log('showVideoPopup 설정됨:', showVideoPopup.value)

    // 챗봇 아바타 새로고침 요청
    requestRefreshAvatar()
    console.log('챗봇 아바타 새로고침 요청')

    // 상단으로 스크롤
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (err) {
    console.error("제출 실패:", err)
    error(err.response?.data?.detail || "제출에 실패했습니다.")
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
    gender: "",
    age: null,
    income: null,
    savings: null,
    investment_goal: "",
    investment_period: null,
  }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 성별 텍스트
const getGenderText = (gender) => {
  return gender === 'M' ? '남성' : '여성'
}

// 유형별 아이콘 (6가지)
const getTypeIcon = (riskType) => {
  const icons = {
    timid_male: "🛡️",
    normal_male: "⚖️",
    speculative_male: "🚀",
    timid_female: "🛡️",
    normal_female: "⚖️",
    speculative_female: "🚀",
  }
  return icons[riskType] || "📊"
}

// 유형 키 (스타일링용)
const getTypeKey = (riskType) => {
  if (riskType?.includes('timid')) return 'timid'
  if (riskType?.includes('normal')) return 'normal'
  if (riskType?.includes('speculative')) return 'speculative'
  return 'normal'
}

onMounted(() => {
  fetchQuestions()
})
</script>

<style scoped>
.survey-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 60px 20px;
  min-height: 100vh;
}

/* Header */
.survey-header {
  text-align: center;
  margin-bottom: 48px;
}

.header-badge {
  display: inline-block;
  padding: 6px 16px;
  background: linear-gradient(135deg, #667eea 0%, #3d66eb 100%);
  color: white;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
  border-radius: 20px;
  margin-bottom: 16px;
}

.survey-header h1 {
  font-size: 36px;
  font-weight: 800;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #667eea 0%, #0e0d0d 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.survey-description {
  font-size: 16px;
  color: #6b7280;
  line-height: 1.6;
}

.highlight {
  color: #667eea;
  font-weight: 600;
}

/* Progress */
.progress-section {
  margin-bottom: 48px;
}

.progress-bar {
  position: relative;
  height: 12px;
  background: #e5e7eb;
  border-radius: 100px;
  overflow: hidden;
}

.progress-fill {
  position: relative;
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #3d66eb 100%);
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 100px;
}

.progress-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 100px;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4));
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100px); }
  100% { transform: translateX(100px); }
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  font-size: 14px;
  font-weight: 600;
}

.progress-text {
  color: #667eea;
}

.progress-percent {
  color: #9ca3af;
}

/* Loading */
.loading {
  text-align: center;
  padding: 80px 20px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading p {
  color: #6b7280;
  font-size: 16px;
}

/* Step Header */
.step-header {
  margin-bottom: 40px;
}

.step-number {
  display: inline-block;
  padding: 4px 12px;
  background: #eef2ff;
  color: #667eea;
  font-size: 12px;
  font-weight: 700;
  border-radius: 12px;
  margin-bottom: 12px;
}

.step-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 8px;
}

.step-description {
  font-size: 15px;
  color: #6b7280;
}

/* Gender Selection */
.gender-group {
  margin-bottom: 32px;
}

.gender-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.gender-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
}

.gender-btn:hover {
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.gender-btn.selected {
  border-color: #667eea;
  background: linear-gradient(135deg, #eef2ff 0%, #f3f0ff 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.gender-icon {
  font-size: 48px;
}

.gender-text {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.gender-btn.selected .gender-text {
  color: #667eea;
}

/* Form */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #374151;
}

.form-group label.required::after {
  content: " *";
  color: #ef4444;
}

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  width: 100%;
  padding: 14px 60px 14px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 16px;
  transition: all 0.2s;
  background: white;
}

.input-wrapper input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.input-unit {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  font-size: 14px;
  font-weight: 500;
}

.select-input {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 16px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.select-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Question */
.question-header {
  margin-bottom: 32px;
}

.question-badge {
  display: inline-block;
  padding: 6px 14px;
  background: #f3f0ff;
  color: #3d66eb;
  font-size: 12px;
  font-weight: 700;
  border-radius: 20px;
  margin-bottom: 16px;
}

.question-number {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 8px;
}

.question-text {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  line-height: 1.4;
}

/* Choices */
.choices {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 40px;
}

.choice-button {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
}

.choice-button:hover {
  border-color: #667eea;
  background: #f9fafb;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.choice-button.selected {
  border-color: #667eea;
  background: linear-gradient(135deg, #eef2ff 0%, #f3f0ff 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.choice-marker {
  flex-shrink: 0;
}

.choice-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: #f3f4f6;
  border-radius: 50%;
  font-weight: 700;
  font-size: 15px;
  color: #6b7280;
}

.choice-button.selected .choice-number {
  background: #667eea;
  color: white;
}

.choice-text {
  flex: 1;
  font-size: 15px;
  color: #374151;
  line-height: 1.6;
}

.choice-button.selected .choice-text {
  color: #111827;
  font-weight: 500;
}

.check-icon {
  flex-shrink: 0;
  color: #667eea;
}

/* Navigation */
.survey-navigation {
  display: flex;
  gap: 16px;
}

.btn-primary,
.btn-secondary,
.btn-outline {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px 24px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #3d66eb 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: white;
  color: #667eea;
  border: 2px solid #e5e7eb;
}

.btn-secondary:hover:not(:disabled) {
  border-color: #667eea;
  background: #f9fafb;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  font-size: 18px;
}

/* Result */
.result-container {
  animation: fadeIn 0.6s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-card {
  background: white;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
}

.result-header {
  position: relative;
  height: 360px; /* 🔥 빨간 네모 크기 */
  padding: 32px;
  border-radius: 24px;
  overflow: hidden;

  background-size: contain;   /* 캐릭터 전체 보이게 */
  background-position: center bottom;
  background-repeat: no-repeat;

  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.result-header::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.1;
  background-image: radial-gradient(circle at 20% 50%, white 2px, transparent 2px);
  background-size: 30px 30px;
}

.result-header::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to top,
    rgba(0,0,0,0),
    rgba(0,0,0,0),
    transparent
  );
}

.result-icon {
  font-size: 80px;
  margin-bottom: 20px;
  animation: bounce 1s ease-in-out;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.result-title {
  position: relative;
  z-index: 1;
}

.result-label {
  display: block;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 8px;
  font-weight: 500;
}

.result-type {
  font-size: 20px;
  font-weight: 800;
  color: rgb(19, 18, 18);
  margin: 0;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.result-badge {
  display: inline-block;
  margin-top: 16px;
  padding: 8px 20px;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  border-radius: 20px;
}

.badge-text {
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.result-body {
  padding: 32px;
}

.result-section {
  margin-bottom: 32px;
  padding: 24px;
  background: #f9fafb;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
}

.result-section:last-child {
  margin-bottom: 0;
}

.section-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.result-section h3 {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 16px;
}

.section-text {
  font-size: 15px;
  color: #4b5563;
  line-height: 1.7;
}

.characteristics-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.characteristics-list li {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #e5e7eb;
}

.characteristics-list li:last-child {
  border-bottom: none;
}

.char-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #3d66eb;
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
}

.char-text {
  flex: 1;
  font-size: 15px;
  color: #374151;
  line-height: 1.6;
}

.recommendation-section {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-color: #fbbf24;
}

.products-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.product-tag {
  padding: 8px 16px;
  background: white;
  border: 2px solid #fbbf24;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  color: #d97706;
}

.result-actions {
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-top: 1px solid #e5e7eb;
}

.btn-large {
  padding: 18px 32px;
  font-size: 18px;
}

.btn-outline {
  background: white;
  color: #6b7280;
  border: 2px solid #e5e7eb;
}

.btn-outline:hover {
  border-color: #667eea;
  color: #667eea;
  background: #f9fafb;
}

/* Responsive */
@media (max-width: 768px) {
  .survey-container {
    padding: 40px 16px;
  }

  .survey-header h1 {
    font-size: 28px;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .question-text {
    font-size: 20px;
  }

  .result-type {
    font-size: 32px;
  }

  .result-actions {
    padding: 24px 16px;
  }
}

.character-image {
  width: 120px;
  height: 120px;
  object-fit: contain;
  margin-bottom: 20px;
  animation: bounce 1s ease-in-out;
}
</style>
