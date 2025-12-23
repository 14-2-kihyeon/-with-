<!-- src/views/auth/RecommendationsView.vue -->
<template>
  <div class="recommendations-container">
    <!-- 헤더 -->
    <div class="recommendations-header">
      <div class="header-left">
        <h1>💎 맞춤 상품 추천</h1>
        <p class="subtitle">당신의 투자 성향에 맞는 최적의 금융 상품을 찾아드립니다</p>
      </div>
      <div v-if="profile" class="header-right">
        <div class="user-profile-badge">
          <span class="badge-icon">{{ getRiskIcon(profile.risk_type) }}</span>
          <div class="badge-info">
            <span class="badge-label">투자 성향</span>
            <span class="badge-value">{{ profile.risk_type_name }}</span>
          </div>
        </div>
        <button class="btn-retake" @click="goToSurvey">
          <span class="btn-icon">🔄</span>
          재검사하기
        </button>
      </div>
    </div>

    <!-- 투자 성향 미등록 -->
    <div v-if="!profile && !loading" class="empty-state">
      <div class="empty-icon">📊</div>
      <h2>투자 성향 검사가 필요합니다</h2>
      <p>맞춤 상품 추천을 받으려면 먼저 투자 성향 검사를 진행해주세요.</p>
      <button class="btn-primary btn-large" @click="goToSurvey">
        <span class="btn-icon">📝</span>
        투자 성향 검사 시작하기
      </button>
    </div>

    <!-- 로딩 -->
    <div v-else-if="loading" class="loading">
      <div class="spinner"></div>
      <p>맞춤 상품을 분석하는 중...</p>
    </div>

    <!-- 추천 콘텐츠 -->
    <div v-else class="recommendations-content">
      <!-- 프로필 요약 카드 -->
      <div class="profile-summary-card" :class="`type-${getTypeClass(profile.risk_type)}`">
        <div class="summary-header">
          <div class="header-icon">{{ getRiskIcon(profile.risk_type) }}</div>
          <div class="header-text">
            <h2>{{ profile.risk_type_name }} 투자자</h2>
            <p class="score-display">투자 성향 점수: <strong>{{ profile.risk_score}}점</strong></p>
          </div>
          <div class="gender-badge">{{ profile.gender_display }}</div>
        </div>

        <div class="profile-stats">
          <div class="stat-item">
            <div class="stat-icon">🎯</div>
            <div class="stat-content">
              <span class="stat-label">투자 목표</span>
              <span class="stat-value">{{ profile.investment_goal || '-' }}</span>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon">⏱️</div>
            <div class="stat-content">
              <span class="stat-label">투자 기간</span>
              <span class="stat-value">{{ profile.investment_period }}개월</span>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon">💰</div>
            <div class="stat-content">
              <span class="stat-label">현재 저축액</span>
              <span class="stat-value">{{ formatCurrency(profile.savings) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 투자 계획 섹션 -->
      <div v-if="investmentPlan" class="investment-plan-section">
        <div class="section-header">
          <h2><span class="header-icon">📋</span> 맞춤 투자 계획</h2>
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
                <div class="step-period">{{ step.period }}</div>
                <div class="step-action">{{ step.action }}</div>
                <div class="step-description">{{ step.description }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 투자 팁 -->
        <div class="plan-tips">
          <h3>💡 투자 성공 팁</h3>
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
          <h2><span class="header-icon">🎁</span> 추천 금융 상품</h2>
          <p class="section-subtitle">총 {{ totalCount }}개 상품 중 상위 매칭 상품을 보여드립니다</p>
        </div>

        <div class="recommendations-grid">
          <div
            v-for="(rec, index) in recommendations"
            :key="`${rec.product.fin_prdt_cd}-${rec.option.save_trm}`"
            class="recommendation-card"
          >
            <div class="card-rank">
              <div class="rank-badge">{{ index + 1 }}</div>
              <div class="match-score">
                <div class="score-circle" :style="{ '--score': rec.match_score }">
                  <span>{{ rec.match_score }}</span>
                </div>
                <span class="score-label">매칭도</span>
              </div>
            </div>

            <div class="card-body">
              <div class="bank-name">{{ rec.product.kor_co_nm }}</div>
              <h3 class="product-name">{{ rec.product.fin_prdt_nm }}</h3>

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

              <div class="recommendation-reason">
                <div class="reason-icon">💬</div>
                <p>{{ rec.reason }}</p>
              </div>

              <div class="product-details">
                <div v-if="rec.product.join_way" class="detail-row">
                  <span class="detail-label">가입방법</span>
                  <span class="detail-value">{{ rec.product.join_way }}</span>
                </div>
              </div>

              <div v-if="rec.product.spcl_cnd" class="special-condition">
                <div class="condition-header">
                  <span class="condition-icon">⭐</span>
                  <span class="condition-title">우대조건</span>
                </div>
                <p class="condition-text">{{ rec.product.spcl_cnd }}</p>
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
          <div class="empty-icon">📭</div>
          <p>현재 조건에 맞는 추천 상품이 없습니다.</p>
          <p class="empty-hint">투자 기간이나 조건을 변경하여 다시 검색해보세요.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import api from "@/api/axios"

const router = useRouter()

// 상태
const loading = ref(false)
const profile = ref(null)
const recommendations = ref([])
const investmentPlan = ref(null)
const totalCount = ref(0)
const bookmarkedProducts = ref(new Set())

// Methods
const fetchRecommendations = async () => {
  loading.value = true
  try {
    const res = await api.get("/accounts/recommendations/")
    profile.value = res.data.profile
    recommendations.value = res.data.recommendations || []
    investmentPlan.value = res.data.investment_plan
    totalCount.value = res.data.total_count || 0
  } catch (error) {
    if (error.response?.status === 404) {
      // 투자 성향 미등록
      profile.value = null
    } else {
      console.error("추천 상품 로딩 실패:", error)
      alert(error.response?.data?.detail || "추천 상품을 불러올 수 없습니다.")
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

    // 북마크 상태 토글
    if (bookmarkedProducts.value.has(finPrdtCd)) {
      bookmarkedProducts.value.delete(finPrdtCd)
    } else {
      bookmarkedProducts.value.add(finPrdtCd)
    }
  } catch (error) {
    console.error("북마크 실패:", error)
    alert("북마크에 실패했습니다.")
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

const getRiskIcon = (riskType) => {
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

.header-left h1 {
  font-size: 36px;
  font-weight: 800;
  color: #0f172a;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 16px;
  color: #64748b;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
  color: white;
}

.badge-icon {
  font-size: 32px;
}

.badge-label {
  display: block;
  font-size: 12px;
  opacity: 0.9;
  margin-bottom: 2px;
}

.badge-value {
  display: block;
  font-size: 18px;
  font-weight: 700;
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
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
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

.empty-icon {
  font-size: 96px;
  margin-bottom: 24px;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.4);
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
  border-top-color: #667eea;
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
  border-color: #c4b5fd;
  background: linear-gradient(135deg, #ffffff 0%, #f5f3ff 100%);
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

.header-icon {
  font-size: 56px;
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
  color: #667eea;
  font-weight: 700;
}

.gender-badge {
  margin-left: auto;
  padding: 8px 16px;
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
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
  padding: 16px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.stat-icon {
  font-size: 32px;
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
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 8px;
}

.header-icon {
  font-size: 28px;
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
  border-left: 4px solid #667eea;
  transition: all 0.3s;
}

.step-item:hover {
  background: #eff6ff;
  transform: translateX(4px);
}

.step-number {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  font-size: 16px;
  font-weight: 700;
}

.step-content {
  flex: 1;
}

.step-period {
  font-size: 12px;
  color: #667eea;
  font-weight: 600;
  margin-bottom: 4px;
}

.step-action {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 6px;
}

.step-description {
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
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
}

.recommendation-card:hover {
  border-color: #667eea;
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.15);
  transform: translateY(-4px);
}

.card-rank {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 2px solid #e2e8f0;
}

.rank-badge {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 700;
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
  margin-bottom: 20px;
  line-height: 1.4;
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
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #fffbeb;
  border-radius: 12px;
  margin-bottom: 16px;
}

.reason-icon {
  font-size: 20px;
}

.recommendation-reason p {
  font-size: 14px;
  color: #92400e;
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
  background: #f0fdf4;
  border-radius: 12px;
  border-left: 3px solid #10b981;
}

.condition-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.condition-icon {
  font-size: 18px;
}

.condition-title {
  font-size: 13px;
  font-weight: 700;
  color: #047857;
}

.condition-text {
  font-size: 13px;
  color: #065f46;
  line-height: 1.6;
  margin: 0;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
}

.btn-detail:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
}

.empty-recommendations {
  text-align: center;
  padding: 80px 40px;
}

.empty-recommendations .empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
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
