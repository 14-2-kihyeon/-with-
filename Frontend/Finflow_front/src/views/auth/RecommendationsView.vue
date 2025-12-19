<!-- src/views/finances/RecommendationsView.vue -->
<template>
  <div class="recommendations-container">
    <div class="recommendations-header">
      <h1>맞춤 상품 추천</h1>
      <div v-if="profile" class="user-profile-badge">
        <span class="badge-icon">{{ getRiskIcon(profile.risk_type) }}</span>
        <div>
          <span class="badge-label">투자 성향</span>
          <span class="badge-value">{{ profile.risk_type_name }}</span>
        </div>
      </div>
    </div>

    <!-- 투자 성향 미등록 -->
    <div v-if="!profile && !loading" class="empty-state">
      <div class="empty-icon">📊</div>
      <h2>투자 성향 검사가 필요합니다</h2>
      <p>맞춤 상품 추천을 받으려면 먼저 투자 성향 검사를 진행해주세요.</p>
      <button class="btn-primary" @click="goToSurvey">
        투자 성향 검사하러 가기
      </button>
    </div>

    <!-- 로딩 -->
    <div v-else-if="loading" class="loading">
      <p>추천 상품을 분석하는 중...</p>
    </div>

    <!-- 추천 상품 목록 -->
    <div v-else class="recommendations-content">
      <!-- 성향 요약 -->
      <div class="profile-summary">
        <h2>{{ profile.risk_type_name }} 투자자를 위한 추천</h2>
        <p>{{ getRiskDescription(profile.risk_type) }}</p>
        <div class="profile-details">
          <div class="detail-item">
            <span class="detail-label">투자 목표</span>
            <span class="detail-value">{{ profile.investment_goal || '-' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">투자 기간</span>
            <span class="detail-value">{{ profile.investment_period }}개월</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">위험 점수</span>
            <span class="detail-value">{{ profile.risk_score }}점</span>
          </div>
        </div>
      </div>

      <!-- 추천 상품 카드 -->
      <div class="recommendations-grid">
        <div 
          v-for="(rec, index) in recommendations" 
          :key="rec.product.fin_prdt_cd"
          class="recommendation-card"
        >
          <div class="card-header">
            <div class="rank-badge">TOP {{ index + 1 }}</div>
            <div class="match-score">
              <span class="score-label">매칭도</span>
              <span class="score-value">{{ rec.match_score }}%</span>
            </div>
          </div>

          <div class="card-body">
            <div class="bank-name">{{ rec.product.kor_co_nm }}</div>
            <h3 class="product-name">{{ rec.product.fin_prdt_nm }}</h3>

            <div class="product-rates">
              <div class="rate-item">
                <span class="rate-label">기본 금리</span>
                <span class="rate-value">{{ rec.best_option.intr_rate }}%</span>
              </div>
              <div class="rate-item highlight">
                <span class="rate-label">최고 우대금리</span>
                <span class="rate-value">{{ rec.best_option.intr_rate2 }}%</span>
              </div>
              <div class="rate-item">
                <span class="rate-label">가입 기간</span>
                <span class="rate-value">{{ rec.best_option.save_trm }}개월</span>
              </div>
            </div>

            <div class="recommendation-reason">
              <p>{{ rec.recommended_reason }}</p>
            </div>

            <div class="product-details">
              <div v-if="rec.product.join_way" class="detail-row">
                <strong>가입 방법:</strong>
                <span>{{ rec.product.join_way }}</span>
              </div>
              <div v-if="rec.product.spcl_cnd" class="detail-row special-condition">
                <strong>우대 조건:</strong>
                <span>{{ rec.product.spcl_cnd }}</span>
              </div>
            </div>
          </div>

          <div class="card-footer">
            <button 
              class="btn-bookmark"
              :class="{ bookmarked: isBookmarked(rec.product.fin_prdt_cd) }"
              @click="toggleBookmark(rec.product.fin_prdt_cd)"
            >
              {{ isBookmarked(rec.product.fin_prdt_cd) ? '❤️ 관심상품' : '🤍 관심등록' }}
            </button>
            <button 
              class="btn-detail"
              @click="goToDetail(rec.product.fin_prdt_cd)"
            >
              상세보기
            </button>
          </div>
        </div>
      </div>

      <!-- 추천 상품 없음 -->
      <div v-if="recommendations.length === 0" class="empty-recommendations">
        <p>추천할 수 있는 상품이 없습니다.</p>
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
const bookmarkedProducts = ref(new Set())

// Methods
const fetchProfile = async () => {
  try {
    const res = await api.get("/accounts/investment-profile/")
    profile.value = res.data
  } catch (error) {
    if (error.response?.status === 404) {
      // 투자 성향 미등록
      profile.value = null
    } else {
      console.error("프로필 로딩 실패:", error)
    }
  }
}

const fetchRecommendations = async () => {
  loading.value = true
  try {
    const res = await api.get("/accounts/recommendations/")
    recommendations.value = res.data.recommendations || []
  } catch (error) {
    console.error("추천 상품 로딩 실패:", error)
    alert(error.response?.data?.detail || "추천 상품을 불러올 수 없습니다.")
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
    very_conservative: "🛡️",
    conservative: "🏦",
    moderate: "⚖️",
    aggressive: "📈",
    very_aggressive: "🚀",
  }
  return icons[riskType] || "📊"
}

const getRiskDescription = (riskType) => {
  const descriptions = {
    very_conservative: "안정성을 최우선으로 하는 투자자에게 적합합니다.",
    conservative: "낮은 위험으로 안정적인 수익을 추구합니다.",
    moderate: "위험과 수익의 균형을 맞춘 상품입니다.",
    aggressive: "높은 수익을 위해 적극적으로 투자합니다.",
    very_aggressive: "최대 수익을 목표로 하는 공격적 투자입니다.",
  }
  return descriptions[riskType] || ""
}

onMounted(async () => {
  await fetchProfile()
  if (profile.value) {
    await Promise.all([
      fetchRecommendations(),
      fetchBookmarks(),
    ])
  }
})
</script>

<style scoped>
.recommendations-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.recommendations-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
}

.recommendations-header h1 {
  font-size: 32px;
  font-weight: bold;
  color: #1a1a1a;
}

.user-profile-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.badge-icon {
  font-size: 32px;
}

.badge-label {
  display: block;
  font-size: 12px;
  opacity: 0.9;
}

.badge-value {
  display: block;
  font-size: 18px;
  font-weight: 600;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 24px;
}

.empty-state h2 {
  font-size: 24px;
  margin-bottom: 12px;
  color: #1a1a1a;
}

.empty-state p {
  font-size: 16px;
  color: #666;
  margin-bottom: 32px;
}

/* Profile Summary */
.profile-summary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px;
  border-radius: 16px;
  margin-bottom: 40px;
}

.profile-summary h2 {
  font-size: 28px;
  margin-bottom: 12px;
}

.profile-summary > p {
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 32px;
}

.profile-details {
  display: flex;
  gap: 32px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 12px;
  opacity: 0.8;
}

.detail-value {
  font-size: 20px;
  font-weight: 600;
}

/* Recommendations Grid */
.recommendations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 24px;
  margin-top: 32px;
}

.recommendation-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s;
}

.recommendation-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transform: translateY(-4px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.rank-badge {
  font-size: 14px;
  font-weight: 700;
  color: #4f46e5;
  background: #eef2ff;
  padding: 4px 12px;
  border-radius: 12px;
}

.match-score {
  text-align: right;
}

.score-label {
  display: block;
  font-size: 11px;
  color: #6b7280;
}

.score-value {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: #10b981;
}

.card-body {
  padding: 24px;
}

.bank-name {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 8px;
}

.product-name {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 20px;
}

.product-rates {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 12px;
}

.rate-item {
  text-align: center;
}

.rate-item.highlight {
  background: #eef2ff;
  padding: 8px;
  border-radius: 8px;
}

.rate-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.rate-value {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: #4f46e5;
}

.recommendation-reason {
  padding: 16px;
  background: #fffbeb;
  border-left: 4px solid #f59e0b;
  border-radius: 8px;
  margin-bottom: 16px;
}

.recommendation-reason p {
  font-size: 14px;
  color: #92400e;
  line-height: 1.6;
  margin: 0;
}

.product-details {
  font-size: 14px;
  color: #4b5563;
}

.detail-row {
  margin-bottom: 12px;
  line-height: 1.6;
}

.detail-row strong {
  display: inline-block;
  min-width: 90px;
  color: #1f2937;
}

.special-condition {
  padding: 12px;
  background: #f0fdf4;
  border-radius: 8px;
  border-left: 3px solid #10b981;
}

.card-footer {
  display: flex;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
}

.btn-bookmark,
.btn-detail {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-bookmark {
  background: white;
  border: 1px solid #e5e7eb;
  color: #6b7280;
}

.btn-bookmark.bookmarked {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #dc2626;
}

.btn-detail {
  background: #4f46e5;
  color: white;
}

.btn-detail:hover {
  background: #4338ca;
}

.btn-primary {
  padding: 14px 32px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary:hover {
  background: #4338ca;
}

.loading {
  text-align: center;
  padding: 80px 20px;
  color: #666;
}

.empty-recommendations {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}
</style>