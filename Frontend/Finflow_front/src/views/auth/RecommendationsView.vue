<!-- src/views/auth/RecommendationsView.vue -->
<template>
  <div class="recommendations-container">
    <!-- Alert Modal -->
    <AlertModal
      v-model="showAlert"
      :icon="alertConfig.icon"
      :title="alertConfig.title"
      :message="alertConfig.message"
      :confirm-text="alertConfig.confirmText"
      @confirm="alertConfig.onConfirm"
    />

    <!-- 헤더 -->
    <div class="recommendations-header">
      <div class="header-left">
        <div class="title-wrapper">
          <div class="title-accent"></div>
          <h1>맞춤 상품 추천</h1>
        </div>
        <p class="subtitle">당신의 투자 성향에 맞는 최적의 금융 상품을 찾아드립니다</p>
      </div>
      <div v-if="profile" class="header-right">
        <div class="user-profile-badge">
          <div class="badge-type-indicator" :class="getTypeClass(profile.risk_type)"></div>
          <div class="badge-info">
            <span class="badge-label">투자 성향</span>
            <span class="badge-value">{{ profile.risk_type_name }}</span>
          </div>
        </div>
        <button class="btn-pdf" @click="downloadPDF" :disabled="pdfGenerating">
          <svg v-if="!pdfGenerating" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M6 2C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V16C4 16.5304 4.21071 17.0391 4.58579 17.4142C4.96086 17.7893 5.46957 18 6 18H14C14.5304 18 15.0391 17.7893 15.4142 17.4142C15.7893 17.0391 16 16.5304 16 16V7.414C16 7.01478 15.842 6.63211 15.5607 6.35078L11.6464 2.43645C11.3651 2.15512 10.9824 1.99701 10.5832 1.99701L6 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M10 2V6C10 6.26522 10.1054 6.51957 10.2929 6.70711C10.4804 6.89464 10.7348 7 11 7H16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <div v-else class="spinner-small"></div>
          <span>{{ pdfGenerating ? 'PDF 생성 중...' : 'PDF 다운로드' }}</span>
        </button>
        <button class="btn-retake" @click="goToSurvey">
          재검사하기
        </button>
      </div>
    </div>

    <!-- 투자 성향 미등록 -->
    <div v-if="!profile && !loading" class="empty-state">
      <div class="empty-icon-circle">
        <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
          <rect x="8" y="24" width="8" height="32" rx="2" fill="#cbd5e1"/>
          <rect x="20" y="16" width="8" height="40" rx="2" fill="#94a3b8"/>
          <rect x="32" y="20" width="8" height="36" rx="2" fill="#64748b"/>
          <rect x="44" y="12" width="8" height="44" rx="2" fill="#3b82f6"/>
        </svg>
      </div>
      <h2>투자 성향 검사가 필요합니다</h2>
      <p>맞춤 상품 추천을 받으려면 먼저 투자 성향 검사를 진행해주세요.</p>
      <button class="btn-primary btn-large" @click="goToSurvey">
        투자 성향 검사 시작하기
      </button>
    </div>

    <!-- 로딩 -->
    <div v-else-if="loading" class="loading">
      <div class="spinner"></div>
      <p>맞춤 상품을 분석하는 중...</p>
    </div>

    <!-- 추천 콘텐츠 -->
    <div v-else ref="pdfContent" class="recommendations-content">
      <!-- 프로필 요약 카드 -->
      <div class="profile-summary-card" :class="`type-${getTypeClass(profile.risk_type)}`">
        <div class="summary-header">
          <img
            :src="getCharacterImage(profile.risk_type)"
            :alt="profile.risk_type_name"
            class="character-image"
          />
          <div class="header-text">
            <h2>{{ auth.user?.username || '투자자' }}님의 프로필</h2>
            <p class="score-display">{{ profile.risk_type_name }} · 성향 점수: <strong>{{ profile.risk_score}}점</strong></p>
          </div>
          <div class="gender-badge">{{ profile.gender_display }}</div>
        </div>

        <div class="profile-stats">
          <div class="stat-item">
            <div class="stat-content">
              <span class="stat-label">투자 목표</span>
              <span class="stat-value">{{ profile.investment_goal || '-' }}</span>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-content">
              <span class="stat-label">투자 기간</span>
              <span class="stat-value">{{ profile.investment_period }}개월</span>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-content">
              <span class="stat-label">현재 저축액</span>
              <span class="stat-value">{{ formatCurrency(profile.savings) }}</span>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-content">
              <span class="stat-label">투자 금액</span>
              <span class="stat-value">{{ formatCurrency(profile.investment_amount || profile.savings) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 투자 계획 섹션 -->
      <div v-if="investmentPlan" class="investment-plan-section">
        <div class="section-header">
          <h2>맞춤 투자 계획</h2>
          <p class="section-subtitle">{{ investmentPlan.total_period_months }}개월 동안의 투자 전략을 제시합니다</p>
        </div>

        <div class="plan-strategy">
          <div class="strategy-badge">전략</div>
          <p>{{ investmentPlan.strategy }}</p>
        </div>

        <!-- 투자 단계 -->
        <div class="plan-steps">
          <h3>단계별 실행 계획</h3>
          <div class="steps-timeline">
            <div
              v-for="(step, index) in investmentPlan.steps"
              :key="index"
              class="step-item"
            >
              <div class="step-number">{{ index + 1 }}</div>
              <div class="step-content">
                <div class="step-header">
                  <div class="step-period">{{ step.period }}</div>
                  <div class="step-action">{{ step.action }}</div>
                </div>
                <div class="step-description">{{ step.description }}</div>
                <!-- 예상 수익 표시 (profile.savings를 기준으로) -->
                <div v-if="step.expected_rate" class="step-profit">
                  <span class="profit-label">예상 수익</span>
                  <span class="profit-value">
                    +{{ calculateProfit(profile.savings, step.expected_rate, step.months || profile.investment_period).toLocaleString() }}만원
                  </span>
                  <span class="profit-rate">(연 {{ step.expected_rate }}%)</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 투자 팁 -->
        <div class="plan-tips">
          <h3>투자 성공 팁</h3>
          <ul class="tips-list">
            <li v-for="(tip, index) in investmentPlan.tips" :key="index">
              <span class="tip-icon">✓</span>
              <span class="tip-text">{{ tip }}</span>
            </li>
          </ul>
        </div>
      </div>

      <!-- 추천 상품 섹션 -->
      <div class="recommendations-section">
        <div class="section-header">
          <h2>추천 금융 상품</h2>
          <p class="section-subtitle">총 {{ totalCount }}개 상품 중 상위 매칭 상품을 보여드립니다</p>
        </div>

        <div class="recommendations-grid">
          <div
            v-for="(rec, index) in uniqueRecommendations"
            :key="rec.product.fin_prdt_cd"
            class="recommendation-card"
          >
            <div class="card-rank">
              <div class="rank-info">
                <div class="rank-badge">{{ index + 1 }}</div>
                <img
                  v-if="getBankLogo(rec.product.kor_co_nm)"
                  :src="getBankLogo(rec.product.kor_co_nm)"
                  :alt="rec.product.kor_co_nm"
                  class="bank-logo"
                />
                <div class="rank-details">
                  <span class="rank-bank">{{ rec.product.kor_co_nm }}</span>
                  <span class="rank-product">{{ cleanProductName(rec.product.fin_prdt_nm) }}</span>
                </div>
              </div>
              <div class="match-score">
                <div class="score-circle" :style="{ '--score': rec.match_score }">
                  <span>{{ rec.match_score }}</span>
                </div>
                <span class="score-label">매칭도</span>
              </div>
            </div>

            <div class="card-body">
              <div class="product-rates">
                <div class="rate-box">
                  <span class="rate-label">기본금리</span>
                  <span class="rate-value">{{ rec.option.intr_rate.toFixed(2) }}%</span>
                </div>
                <div class="rate-box highlight">
                  <span class="rate-label">최고금리</span>
                  <span class="rate-value primary">{{ rec.option.intr_rate2.toFixed(2) }}%</span>
                </div>
                <div class="rate-box">
                  <span class="rate-label">가입기간</span>
                  <span class="rate-value">{{ rec.option.save_trm }}개월</span>
                </div>
              </div>

              <!-- 예상 수익 강조 표시 -->
              <div class="profit-highlight">
                <div class="profit-main">
                  <span class="profit-label">예상 수익</span>
                  <span class="profit-amount">
                    +{{ calculateProfit(profile.savings, rec.option.intr_rate2, rec.option.save_trm).toLocaleString() }}만원
                  </span>
                </div>
                <div class="profit-detail">
                  {{ profile.savings.toLocaleString() }}만원 × {{ rec.option.save_trm }}개월 × 최고금리 {{ rec.option.intr_rate2.toFixed(2) }}%
                </div>
              </div>

              <div class="product-details">
                <div v-if="rec.product.join_way" class="detail-row">
                  <span class="detail-label">가입방법</span>
                  <span class="detail-value">{{ rec.product.join_way }}</span>
                </div>
              </div>

              <!-- 우대조건 구조화 -->
              <div v-if="rec.product.spcl_cnd" class="special-condition">
                <div class="condition-header">
                  <span class="condition-title">우대조건</span>
                </div>
                <ul class="condition-list">
                  <li v-for="(condition, idx) in parseSpecialConditions(rec.product.spcl_cnd)" :key="idx">
                    <span class="condition-bullet"></span>
                    <span class="condition-text">{{ condition }}</span>
                  </li>
                </ul>
              </div>
            </div>

            <div class="card-footer">
              <button
                class="btn-bookmark"
                :class="{ bookmarked: isBookmarked(rec.product.fin_prdt_cd) }"
                @click="toggleBookmark(rec.product.fin_prdt_cd)"
              >
                <span class="btn-icon">{{ isBookmarked(rec.product.fin_prdt_cd) ? '❤️' : '🤍' }}</span>
                {{ isBookmarked(rec.product.fin_prdt_cd) ? '관심상품' : '관심등록' }}
              </button>
              <button
                class="btn-detail"
                @click="goToDetail(rec.product.fin_prdt_cd)"
              >
                자세히 보기 →
              </button>
            </div>
          </div>
        </div>

        <!-- 추천 상품 없음 -->
        <div v-if="recommendations.length === 0" class="empty-recommendations">
          <p>현재 조건에 맞는 추천 상품이 없습니다.</p>
          <p class="empty-hint">투자 기간이나 조건을 변경하여 다시 검색해보세요.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import api from "@/api/axios"
import AlertModal from "@/components/common/AlertModal.vue"
import { useAlert } from "@/composables/useAlert"
import html2pdf from 'html2pdf.js'

// 투자 성향 결과 이미지 import
import timidMale from "@/assets/character/timid_male.png"
import timidFemale from "@/assets/character/timid_female.png"
import normalMale from "@/assets/character/normal_male.png"
import normalFemale from "@/assets/character/normal_female.png"
import speculativeMale from "@/assets/character/speculative_male.png"
import speculativeFemale from "@/assets/character/speculative_female.png"

const router = useRouter()
const auth = useAuthStore()

// Alert composable
const { showAlert, alertConfig, error } = useAlert()

// 상태
const loading = ref(false)
const profile = ref(null)
const recommendations = ref([])
const investmentPlan = ref(null)
const totalCount = ref(0)
const bookmarkedProducts = ref(new Set())
const pdfContent = ref(null)
const pdfGenerating = ref(false)

// 중복 상품 제거 (같은 fin_prdt_cd는 최고 금리 옵션만 표시)
const uniqueRecommendations = computed(() => {
  const seen = new Map()

  for (const rec of recommendations.value) {
    const key = rec.product.fin_prdt_cd
    const existing = seen.get(key)

    // 아직 없거나, 더 높은 금리면 교체
    if (!existing || rec.option.intr_rate2 > existing.option.intr_rate2) {
      seen.set(key, rec)
    }
  }

  return Array.from(seen.values()).slice(0, 9)
})

// Methods
const fetchRecommendations = async () => {
  loading.value = true
  try {
    const res = await api.get("/accounts/recommendations/")
    profile.value = res.data.profile

    // username이 없으면 user 정보에서 가져오기
    if (!profile.value.username && res.data.user) {
      profile.value.username = res.data.user.username
    }

    recommendations.value = res.data.recommendations || []
    investmentPlan.value = res.data.investment_plan
    totalCount.value = res.data.total_count || 0
  } catch (err) {
    if (err.response?.status === 404) {
      // 투자 성향 미등록
      profile.value = null
    } else {
      console.error("추천 상품 로딩 실패:", err)
      error(err.response?.data?.detail || "추천 상품을 불러올 수 없습니다.")
    }
  } finally {
    loading.value = false
  }
}

const fetchBookmarks = async () => {
  try {
    const res = await api.get("/accounts/bookmarks/")
    bookmarkedProducts.value = new Set(res.data.map(b => b.fin_prdt_cd))
  } catch (error) {
    console.error("북마크 로딩 실패:", error)
  }
}

const toggleBookmark = async (finPrdtCd) => {
  try {
    await api.post(`/accounts/recommendations/${finPrdtCd}/bookmark/`)

    // 북마크 상태 토글 (Vue 반응성을 위해 새로운 Set 생성)
    const newSet = new Set(bookmarkedProducts.value)
    if (newSet.has(finPrdtCd)) {
      newSet.delete(finPrdtCd)
    } else {
      newSet.add(finPrdtCd)
    }
    bookmarkedProducts.value = newSet
  } catch (err) {
    console.error("북마크 실패:", err)
    error("북마크에 실패했습니다.")
  }
}

const isBookmarked = (finPrdtCd) => {
  return bookmarkedProducts.value.has(finPrdtCd)
}

const goToDetail = (finPrdtCd) => {
  router.push({ name: "deposit_detail", params: { fin_prdt_cd: finPrdtCd } })
}

const goToSurvey = () => {
  router.push({ name: "investment_survey" })
}

const downloadPDF = async () => {
  if (!pdfContent.value || pdfGenerating.value) return

  try {
    pdfGenerating.value = true

    // PDF 옵션 설정
    const opt = {
      margin: [10, 10, 10, 10],
      filename: `맞춤_상품_추천_${auth.user?.username || '투자자'}_${new Date().toISOString().split('T')[0]}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: {
        scale: 2,
        useCORS: true,
        logging: false,
        letterRendering: true,
        allowTaint: true,
        backgroundColor: '#ffffff'
      },
      jsPDF: {
        unit: 'mm',
        format: 'a4',
        orientation: 'portrait',
        compress: true
      },
      pagebreak: {
        mode: ['avoid-all', 'css', 'legacy'],
        before: '.page-break-before',
        after: '.page-break-after'
      }
    }

    // PDF 생성
    await html2pdf().set(opt).from(pdfContent.value).save()

    console.log('PDF 다운로드 완료')
  } catch (err) {
    console.error('PDF 생성 실패:', err)
    error('PDF 생성에 실패했습니다.')
  } finally {
    pdfGenerating.value = false
  }
}

const getTypeClass = (riskType) => {
  if (riskType?.includes('timid')) return 'timid'
  if (riskType?.includes('normal')) return 'normal'
  if (riskType?.includes('speculative')) return 'speculative'
  return 'normal'
}

const formatCurrency = (amount) => {
  if (!amount) return '-'
  return `${Number(amount).toLocaleString()}만원`
}

// 상품명에서 (만기지급식) 또는 (만기일시지급식) 제거
const cleanProductName = (name) => {
  if (!name) return ''
  return name.replace(/\(만기일?시?지급식\)/g, '').trim()
}

// 예상 수익 계산 함수 (단리)
const calculateProfit = (principal, rate, months) => {
  if (!principal || !rate || !months) return 0
  // 단리 계산: 원금 * (금리/100) * (개월수/12)
  const profit = principal * (rate / 100) * (months / 12)
  return Math.floor(profit)
}

// 복리 적용 예상 총액 계산 함수
const calculateCompoundTotal = (savings, investmentAmount, bestRate, bestPeriod, totalPeriod) => {
  if (!savings || !investmentAmount || !bestRate || !bestPeriod || !totalPeriod) return savings + investmentAmount

  // 최고 상품을 몇 번 반복 가입할 수 있는지 계산
  const n = Math.floor(totalPeriod / bestPeriod)

  // 초기 투자 총액 (현재 저축액 + 투자 금액)
  let total = savings + investmentAmount

  // n번 복리 적용
  for (let i = 0; i < n; i++) {
    total = total * (1 + (bestRate / 100) * (bestPeriod / 12))
  }

  return Math.floor(total)
}

// 우대조건 파싱 함수
const parseSpecialConditions = (conditions) => {
  if (!conditions) return []

  // 1. 번호로 시작하는 조건들 (1., 2., 1), 2) 등)
  const numberedPattern = /\d+[.)]\s*[^1-9]+/g
  let items = conditions.match(numberedPattern)

  if (items && items.length > 1) {
    return items.map(item => item.replace(/^\d+[.)]\s*/, '').trim())
  }

  // 2. 쉼표나 세미콜론으로 구분
  items = conditions.split(/[,;]/)
  if (items.length > 1) {
    return items.map(item => item.trim()).filter(item => item.length > 0)
  }

  // 3. '및', '그리고', '또는'으로 구분
  items = conditions.split(/\s+(?:및|그리고|또는)\s+/)
  if (items.length > 1) {
    return items.map(item => item.trim())
  }

  // 4. 구분할 수 없으면 전체를 하나의 항목으로
  return [conditions.trim()]
}

// 투자 성향 결과 이미지 가져오기
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

// 은행 정보 매핑 테이블
const BANKS = [
  { apiName: "경남은행", logo: "knbank.png" },
  { apiName: "광주은행", logo: "kjbank.png" },
  { apiName: "국민은행", logo: "kb.png" },
  { apiName: "농협은행주식회사", logo: "nh.png" },
  { apiName: "부산은행", logo: "bnk.png" },
  { apiName: "수협은행", logo: "sh.png" },
  { apiName: "신한은행", logo: "shinhan.png" },
  { apiName: "아이엠뱅크", logo: "imbank.png" },
  { apiName: "우리은행", logo: "woori.png" },
  { apiName: "전북은행", logo: "jb.png" },
  { apiName: "제주은행", logo: "jj.png" },
  { apiName: "주식회사 카카오뱅크", logo: "kakao.png" },
  { apiName: "주식회사 케이뱅크", logo: "kbank.png" },
  { apiName: "주식회사 하나은행", logo: "hana.png" },
  { apiName: "중소기업은행", logo: "ibk.png" },
  { apiName: "토스뱅크 주식회사", logo: "toss.png" },
  { apiName: "한국산업은행", logo: "kdb.png" },
  { apiName: "한국스탠다드차타드은행", logo: "sc.png" },
]

const byApiName = new Map(BANKS.map(b => [b.apiName, b]))

// 은행 로고 이미지 경로 가져오기
const getBankLogo = (bankName) => {
  const bank = byApiName.get(bankName)
  if (bank) {
    try {
      return new URL(`../../assets/banks/${bank.logo}`, import.meta.url).href
    } catch {
      return ''
    }
  }
  return ''
}

onMounted(async () => {
  await Promise.all([
    fetchRecommendations(),
    fetchBookmarks(),
  ])
})
</script>

<style scoped>
.recommendations-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 24px 80px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  min-height: 100vh;
}

/* 헤더 */
.recommendations-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 48px;
  gap: 32px;
}

.header-left {
  margin-left: 24px;
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.title-accent {
  width: 6px;
  height: 48px;
  background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 3px;
  flex-shrink: 0;
}

.header-left h1 {
  font-size: 36px;
  font-weight: 800;
  color: #191f28;
  margin: 0;
  position: relative;
}

.subtitle {
  font-size: 16px;
  color: #64748b;
  margin-left: 22px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-profile-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  color: #0f172a;
}

.badge-type-indicator {
  width: 8px;
  height: 40px;
  border-radius: 4px;
  flex-shrink: 0;
}

.badge-type-indicator.timid {
  background: linear-gradient(180deg, #3b82f6 0%, #60a5fa 100%);
}

.badge-type-indicator.normal {
  background: linear-gradient(180deg, #10b981 0%, #34d399 100%);
}

.badge-type-indicator.speculative {
  background: linear-gradient(180deg, #f59e0b 0%, #fbbf24 100%);
}

.badge-label {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 2px;
}

.badge-value {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.btn-pdf {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}

.btn-pdf:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.35);
  transform: translateY(-2px);
}

.btn-pdf:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-pdf svg {
  flex-shrink: 0;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn-retake {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-retake:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  background: #f0f9ff;
}

.btn-icon {
  font-size: 16px;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 120px 40px;
  background: white;
  border-radius: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.empty-icon-circle {
  width: 120px;
  height: 120px;
  margin: 0 auto 24px;
  background: #f8fafc;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state h2 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #0f172a;
}

.empty-state p {
  font-size: 16px;
  color: #64748b;
  margin-bottom: 32px;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 16px 32px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #2563eb;
}

/* Loading */
.loading {
  text-align: center;
  padding: 120px 40px;
}

.spinner {
  width: 48px;
  height: 48px;
  margin: 0 auto 24px;
  border: 4px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading p {
  font-size: 16px;
  color: #64748b;
}

/* 프로필 요약 카드 */
.profile-summary-card {
  background: white;
  border-radius: 24px;
  padding: 32px;
  margin-bottom: 32px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  border: 2px solid transparent;
  transition: all 0.3s;
}

.profile-summary-card.type-timid {
  border-color: #93c5fd;
  background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
}

.profile-summary-card.type-normal {
  border-color: #bfdbfe;
  background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
}

.profile-summary-card.type-speculative {
  border-color: #fdba74;
  background: linear-gradient(135deg, #ffffff 0%, #fff7ed 100%);
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 2px solid #f1f5f9;
}

.character-image {
  width: 100px;
  height: 100px;
  object-fit: contain;
  flex-shrink: 0;
}

.header-text h2 {
  font-size: 28px;
  font-weight: 800;
  color: #0f172a;
  margin-bottom: 4px;
}

.score-display {
  font-size: 14px;
  color: #64748b;
}

.score-display strong {
  color: #0f172a;
  font-weight: 700;
}

.gender-badge {
  margin-left: auto;
  padding: 8px 16px;
  background: #f1f5f9;
  color: #475569;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

.profile-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.stat-item.highlight {
  background: #f8fafc;
  border: 2px solid #0f172a;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

.stat-value {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.stat-value.large {
  font-size: 22px;
}

/* 투자 계획 섹션 */
.investment-plan-section,
.recommendations-section {
  background: white;
  border-radius: 24px;
  padding: 40px;
  margin-bottom: 32px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.section-header {
  margin-bottom: 32px;
}

.section-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 8px;
}

.section-subtitle {
  font-size: 14px;
  color: #64748b;
}

.plan-strategy {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 24px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-radius: 16px;
  border-left: 4px solid #3b82f6;
  margin-bottom: 32px;
}

.strategy-badge {
  padding: 6px 12px;
  background: #3b82f6;
  color: white;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.plan-strategy p {
  font-size: 15px;
  line-height: 1.7;
  color: #1e40af;
  margin: 0;
}

/* 투자 단계 */
.plan-steps {
  margin-bottom: 32px;
}

.plan-steps h3 {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 20px;
}

.steps-timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-item {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  border-left: 4px solid #3b82f6;
  transition: all 0.2s;
}

.step-item:hover {
  background: #f1f5f9;
}

.step-number {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  font-size: 16px;
  font-weight: 700;
}

.step-content {
  flex: 1;
}

.step-header {
  margin-bottom: 8px;
}

.step-period {
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
  margin-bottom: 4px;
}

.step-action {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.step-description {
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 12px;
}

.step-profit {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  border-radius: 8px;
  border-left: 3px solid #10b981;
}

.step-profit .profit-label {
  font-size: 12px;
  color: #065f46;
  font-weight: 600;
}

.step-profit .profit-value {
  font-size: 16px;
  font-weight: 700;
  color: #047857;
}

.step-profit .profit-rate {
  font-size: 12px;
  color: #059669;
  margin-left: auto;
}

/* 투자 팁 */
.plan-tips h3 {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 16px;
}

.tips-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 12px;
}

.tips-list li {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #fffbeb;
  border-radius: 12px;
  border-left: 3px solid #f59e0b;
}

.tip-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fbbf24;
  color: white;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 700;
}

.tip-text {
  font-size: 14px;
  color: #92400e;
  line-height: 1.6;
  flex: 1;
}

/* 추천 상품 그리드 */
.recommendations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 24px;
}

.recommendation-card {
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 20px;
  overflow: hidden;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
}

.recommendation-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.card-rank {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #ffffff;
  border-bottom: 2px solid #f1f5f9;
}

.rank-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.rank-badge {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.bank-logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
  flex-shrink: 0;
}

.rank-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.rank-bank {
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
}

.rank-product {
  font-size: 14px;
  color: #0f172a;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.match-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.score-circle {
  position: relative;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: conic-gradient(
    #10b981 0% calc(var(--score) * 1%),
    #e5e7eb calc(var(--score) * 1%) 100%
  );
  display: flex;
  align-items: center;
  justify-content: center;
}

.score-circle::before {
  content: '';
  position: absolute;
  width: 36px;
  height: 36px;
  background: white;
  border-radius: 50%;
}

.score-circle span {
  position: relative;
  z-index: 1;
  font-size: 14px;
  font-weight: 700;
  color: #10b981;
}

.score-label {
  font-size: 11px;
  color: #64748b;
}

.card-body {
  padding: 24px;
  flex: 1;
}

.bank-name {
  font-size: 13px;
  color: #64748b;
  font-weight: 600;
  margin-bottom: 8px;
}

.product-name {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 16px;
  line-height: 1.4;
}

/* 예상 수익 하이라이트 */
.profit-highlight {
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  margin-bottom: 20px;
}

.profit-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.profit-main .profit-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 600;
}

.profit-main .profit-amount {
  font-size: 24px;
  font-weight: 800;
  color: #0f172a;
}

.profit-detail {
  font-size: 12px;
  color: #64748b;
  text-align: right;
}

.product-rates {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.rate-box {
  padding: 12px;
  background: #f8fafc;
  border-radius: 12px;
  text-align: center;
  transition: all 0.3s;
}

.rate-box.highlight {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 2px solid #3b82f6;
}

.rate-label {
  display: block;
  font-size: 11px;
  color: #64748b;
  margin-bottom: 6px;
}

.rate-value {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.rate-value.primary {
  color: #3b82f6;
  font-size: 20px;
}

.recommendation-reason {
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  margin-bottom: 16px;
  border-left: 3px solid #3b82f6;
}

.recommendation-reason p {
  font-size: 14px;
  color: #475569;
  line-height: 1.6;
  margin: 0;
}

.product-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.detail-label {
  color: #64748b;
  font-weight: 600;
}

.detail-value {
  color: #0f172a;
}

.special-condition {
  padding: 16px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.condition-header {
  margin-bottom: 12px;
}

.condition-title {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.condition-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.condition-list li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.condition-bullet {
  flex-shrink: 0;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #64748b;
  margin-top: 6px;
}

.condition-text {
  font-size: 13px;
  color: #475569;
  line-height: 1.6;
  flex: 1;
  word-break: keep-all;
  overflow-wrap: break-word;
}

.card-footer {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 2px solid #f1f5f9;
}

.btn-bookmark,
.btn-detail {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.btn-bookmark {
  background: white;
  border: 2px solid #e2e8f0;
  color: #64748b;
}

.btn-bookmark:hover {
  border-color: #fca5a5;
  color: #dc2626;
}

.btn-bookmark.bookmarked {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #dc2626;
}

.btn-detail {
  background: #3b82f6;
  color: white;
  border: none;
}

.btn-detail:hover {
  background: #2563eb;
}

.empty-recommendations {
  text-align: center;
  padding: 80px 40px;
}

.empty-recommendations p {
  font-size: 16px;
  color: #64748b;
  margin: 8px 0;
}

.empty-hint {
  font-size: 14px;
  color: #94a3b8;
}

/* 반응형 */
@media (max-width: 768px) {
  .recommendations-header {
    flex-direction: column;
  }

  .header-right {
    width: 100%;
    flex-direction: column;
  }

  .user-profile-badge,
  .btn-retake {
    width: 100%;
    justify-content: center;
  }

  .recommendations-grid {
    grid-template-columns: 1fr;
  }

  .profile-stats {
    grid-template-columns: 1fr;
  }

  .product-rates {
    grid-template-columns: 1fr;
  }
}
</style>
