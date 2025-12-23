<template>
  <div class="mypage">
    <div class="mypage-container">
      <!-- 헤더 -->
      <div class="mypage-header">
        <h1 class="page-title">마이페이지</h1>
        <div class="user-info">
          <div class="user-avatar">
            <img :src="profileImageUrl" :alt="auth.user?.username" class="avatar-image" />
          </div>
          <div class="user-details">
            <div class="username">{{ auth.user?.username }}</div>
            <div class="user-email" v-if="auth.user?.email">{{ auth.user.email }}</div>
          </div>
        </div>
      </div>

      <!-- 투자 성향 섹션 -->
      <section class="section">
        <div class="section-header">
          <h2 class="section-title">
            <span class="section-icon">📊</span>
            투자 성향 분석
          </h2>
          <button
            v-if="investmentProfile"
            class="btn-retest"
            @click="goToSurvey"
          >
            재검사하기
          </button>
        </div>

        <div v-if="loading.profile" class="loading-state">
          <div class="spinner"></div>
          <p>투자 성향 정보를 불러오는 중...</p>
        </div>

        <div v-else-if="!investmentProfile" class="empty-state">
          <div class="empty-icon">📋</div>
          <p class="empty-text">아직 투자 성향 검사를 완료하지 않았습니다.</p>
          <button class="btn-primary" @click="goToSurvey">
            투자 성향 검사하기
          </button>
        </div>

        <div v-else class="profile-card">
          <div class="profile-header">
            <div class="profile-badge" :class="getRiskClass(investmentProfile.risk_type)">
              <span class="badge-icon">{{ getRiskIcon(investmentProfile.risk_type) }}</span>
              <span class="badge-text">{{ investmentProfile.risk_type_name }}</span>
            </div>
            <div class="profile-score">
              <span class="score-label">투자 성향 점수</span>
              <span class="score-value">{{ investmentProfile.risk_score }}점</span>
            </div>
          </div>

          <div class="profile-image-section">
            <img
              :src="getCharacterImage(investmentProfile.risk_type)"
              :alt="investmentProfile.risk_type_name"
              class="profile-character-image"
            />
          </div>

          <div class="profile-stats">
            <div class="stat-item">
              <span class="stat-label">성별</span>
              <span class="stat-value">{{ investmentProfile.gender_display }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">나이</span>
              <span class="stat-value">{{ investmentProfile.age }}세</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">투자 성향</span>
              <span class="stat-value">{{ investmentProfile.risk_type_name }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">투자 목표</span>
              <span class="stat-value">{{ investmentProfile.investment_goal }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">연 소득</span>
              <span class="stat-value">{{ formatMoney(investmentProfile.income) }}만원</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">현재 저축액</span>
              <span class="stat-value">{{ formatMoney(investmentProfile.savings) }}만원</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">투자 기간</span>
              <span class="stat-value">{{ investmentProfile.investment_period }}개월</span>
            </div>
          </div>

          <div class="profile-description">
            <h3 class="desc-title">성향 설명</h3>
            <p class="desc-text">{{ investmentProfile.description }}</p>
          </div>

          <div class="profile-actions">
            <button class="btn-secondary" @click="goToRecommendations">
              맞춤 추천 상품 보기
            </button>
          </div>
        </div>
      </section>

      <!-- 관심 상품 섹션 -->
      <section class="section">
        <div class="section-header">
          <h2 class="section-title">
            <span class="section-icon">❤️</span>
            관심 상품
          </h2>
          <span class="product-count">{{ bookmarkedProducts.length }}개</span>
        </div>

        <div v-if="loading.bookmarks" class="loading-state">
          <div class="spinner"></div>
          <p>관심 상품을 불러오는 중...</p>
        </div>

        <div v-else-if="bookmarkedProducts.length === 0" class="empty-state">
          <div class="empty-icon">📭</div>
          <p class="empty-text">아직 관심 상품이 없습니다.</p>
          <p class="empty-hint">상품 목록에서 관심 상품을 등록해보세요.</p>
          <button class="btn-secondary" @click="goToFinHome">
            상품 둘러보기
          </button>
        </div>

        <div v-else class="products-grid">
          <div
            v-for="product in bookmarkedProducts"
            :key="product.fin_prdt_cd"
            class="product-card"
          >
            <div class="product-header">
              <div class="product-bank">{{ product.kor_co_nm }}</div>
              <button
                class="btn-unbookmark"
                @click="removeBookmark(product.fin_prdt_cd)"
                title="관심 상품 제거"
              >
                ❤️
              </button>
            </div>
            <h3 class="product-name">{{ product.fin_prdt_nm }}</h3>
            <div class="product-date">
              등록일: {{ formatDate(product.bookmarked_at) }}
            </div>
            <div class="product-actions">
              <RouterLink
                :to="{ name: 'deposit_detail', params: { fin_prdt_cd: product.fin_prdt_cd } }"
                class="btn-detail-small"
              >
                자세히 보기 →
              </RouterLink>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import api from "@/api/axios"

// 투자 성향 결과 이미지 import
import timidMale from "@/assets/character/timid_male.png"
import timidFemale from "@/assets/character/timid_female.png"
import normalMale from "@/assets/character/normal_male.png"
import normalFemale from "@/assets/character/normal_female.png"
import speculativeMale from "@/assets/character/speculative_male.png"
import speculativeFemale from "@/assets/character/speculative_female.png"
import defaultImage from "@/assets/main/icon/lego.png"

const router = useRouter()
const auth = useAuthStore()

// 상태
const loading = ref({
  profile: false,
  bookmarks: false
})
const investmentProfile = ref(null)
const bookmarkedProducts = ref([])

// 사용자 이니셜
const userInitial = computed(() => {
  const username = auth.user?.username || ""
  return username.charAt(0).toUpperCase()
})

// 투자 성향 결과 이미지 가져오기
const getCharacterImage = (riskType) => {
  if (!riskType) return defaultImage

  const map = {
    timid_male: timidMale,
    timid_female: timidFemale,
    normal_male: normalMale,
    normal_female: normalFemale,
    speculative_male: speculativeMale,
    speculative_female: speculativeFemale,
  }
  return map[riskType] || defaultImage
}

// 프로필 이미지 (원형용)
const profileImageUrl = computed(() => {
  return investmentProfile.value
    ? getCharacterImage(investmentProfile.value.risk_type)
    : defaultImage
})

// 투자 성향 정보 가져오기
const fetchInvestmentProfile = async () => {
  loading.value.profile = true
  try {
    const res = await api.get("/accounts/investment-profile/")
    investmentProfile.value = res.data
  } catch (error) {
    if (error.response?.status !== 404) {
      console.error("투자 성향 조회 실패:", error)
    }
  } finally {
    loading.value.profile = false
  }
}

// 관심 상품 가져오기
const fetchBookmarkedProducts = async () => {
  loading.value.bookmarks = true
  try {
    const res = await api.get("/accounts/bookmarks/")
    bookmarkedProducts.value = res.data
  } catch (error) {
    console.error("관심 상품 조회 실패:", error)
  } finally {
    loading.value.bookmarks = false
  }
}

// 관심 상품 제거
const removeBookmark = async (finPrdtCd) => {
  try {
    await api.post(`/accounts/recommendations/${finPrdtCd}/bookmark/`)
    bookmarkedProducts.value = bookmarkedProducts.value.filter(
      p => p.fin_prdt_cd !== finPrdtCd
    )
  } catch (error) {
    console.error("북마크 제거 실패:", error)
    alert("관심 상품 제거에 실패했습니다.")
  }
}

// 네비게이션
const goToSurvey = () => {
  router.push({ name: "investment_survey" })
}

const goToRecommendations = () => {
  router.push({ name: "recommendations" })
}

const goToFinHome = () => {
  router.push({ name: "fin_home" })
}

// 유틸리티 함수
const getRiskIcon = (riskType) => {
  const icons = {
    timid_male: "🛡️",
    normal_male: "⚖️",
    speculative_male: "🚀",
    timid_female: "🛡️",
    normal_female: "⚖️",
    speculative_female: "🚀"
  }
  return icons[riskType] || "📊"
}

const getRiskClass = (riskType) => {
  if (riskType?.includes("timid")) return "risk-timid"
  if (riskType?.includes("normal")) return "risk-normal"
  if (riskType?.includes("speculative")) return "risk-speculative"
  return ""
}

const formatMoney = (value) => {
  if (!value) return "0"
  return Number(value).toLocaleString()
}

const formatDate = (dateStr) => {
  if (!dateStr) return ""
  const date = new Date(dateStr)
  return date.toLocaleDateString("ko-KR")
}

// 마운트
onMounted(async () => {
  await Promise.all([
    fetchInvestmentProfile(),
    fetchBookmarkedProducts()
  ])
})
</script>

<style scoped>
.mypage {
  min-height: calc(100vh - 60px);
  background: linear-gradient(135deg, #f5f7fb 0%, #e8ecf4 100%);
  padding: 24px 16px 40px;
}

.mypage-container {
  max-width: 1000px;
  margin: 0 auto;
}

/* 헤더 */
.mypage-header {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 950;
  color: #0f172a;
  margin: 0 0 20px 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3182F6, #2563eb);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 900;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
  overflow: hidden;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-details {
  flex: 1;
}

.username {
  font-size: 20px;
  font-weight: 900;
  color: #0f172a;
  margin-bottom: 4px;
}

.user-email {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
}

/* 섹션 */
.section {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f1f5f9;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 22px;
  font-weight: 950;
  color: #0f172a;
  margin: 0;
}

.section-icon {
  font-size: 24px;
}

.product-count {
  font-size: 14px;
  font-weight: 900;
  color: #3182F6;
  background: #eef4ff;
  padding: 6px 12px;
  border-radius: 999px;
}

/* 버튼 */
.btn-primary,
.btn-secondary,
.btn-retest {
  border: 0;
  border-radius: 10px;
  font-weight: 900;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  padding: 10px 18px;
}

.btn-primary {
  background: linear-gradient(135deg, #3182F6, #2563eb);
  color: #fff;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
}

.btn-primary:hover {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35);
  transform: translateY(-1px);
}

.btn-secondary {
  background: #f8fafc;
  color: #3182F6;
  border: 1.5px solid #e2e8f0;
}

.btn-secondary:hover {
  background: #eef4ff;
  border-color: #3182F6;
}

.btn-retest {
  background: #fff;
  color: #3182F6;
  border: 1.5px solid #3182F6;
  font-size: 13px;
  padding: 8px 14px;
}

.btn-retest:hover {
  background: #eef4ff;
}

/* 로딩/비어있음 상태 */
.loading-state,
.empty-state {
  text-align: center;
  padding: 48px 24px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #3182F6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p,
.empty-text {
  font-size: 16px;
  font-weight: 700;
  color: #64748b;
  margin: 0;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-hint {
  font-size: 14px;
  font-weight: 600;
  color: #94a3b8;
  margin: 8px 0 24px;
}

/* 투자 성향 카드 */
.profile-card {
  background: linear-gradient(135deg, #fefeff 0%, #f8fafc 100%);
  border-radius: 12px;
  padding: 24px;
  border: 1.5px solid #e2e8f0;
}

.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.profile-image-section {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
}

.profile-character-image {
  max-width: 200px;
  max-height: 200px;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 8px;
}

.profile-badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-radius: 999px;
  font-size: 18px;
  font-weight: 950;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.profile-badge.risk-timid {
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  color: #1e40af;
}

.profile-badge.risk-normal {
  background: linear-gradient(135deg, #e9d5ff, #d8b4fe);
  color: #7c3aed;
}

.profile-badge.risk-speculative {
  background: linear-gradient(135deg, #fed7aa, #fdba74);
  color: #c2410c;
}

.badge-icon {
  font-size: 24px;
}

.profile-score {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.score-label {
  font-size: 13px;
  font-weight: 700;
  color: #64748b;
}

.score-value {
  font-size: 28px;
  font-weight: 950;
  color: #3182F6;
}

/* 통계 */
.profile-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  background: #fff;
  border-radius: 10px;
  padding: 14px 16px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-label {
  font-size: 12px;
  font-weight: 700;
  color: #94a3b8;
}

.stat-value {
  font-size: 16px;
  font-weight: 950;
  color: #0f172a;
}

/* 설명 */
.profile-description {
  background: #f8fafc;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 20px;
}

.desc-title {
  font-size: 14px;
  font-weight: 900;
  color: #475569;
  margin: 0 0 8px 0;
}

.desc-text {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  line-height: 1.6;
  margin: 0;
}

.profile-actions {
  display: flex;
  justify-content: center;
}

/* 상품 그리드 */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.product-card {
  background: linear-gradient(135deg, #fefeff 0%, #f8fafc 100%);
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  padding: 18px;
  transition: all 0.2s ease;
}

.product-card:hover {
  border-color: #3182F6;
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.15);
  transform: translateY(-2px);
}

.product-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.product-bank {
  font-size: 13px;
  font-weight: 900;
  color: #64748b;
}

.btn-unbookmark {
  border: 0;
  background: transparent;
  cursor: pointer;
  font-size: 20px;
  padding: 4px;
  line-height: 1;
  transition: transform 0.2s ease;
}

.btn-unbookmark:hover {
  transform: scale(1.2);
}

.product-name {
  font-size: 16px;
  font-weight: 950;
  color: #0f172a;
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.product-date {
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 16px;
}

.product-actions {
  display: flex;
  justify-content: flex-end;
}

.btn-detail-small {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 14px;
  border-radius: 8px;
  background: linear-gradient(135deg, #3182F6, #2563eb);
  color: #fff;
  font-size: 13px;
  font-weight: 900;
  text-decoration: none;
  transition: all 0.2s ease;
}

.btn-detail-small:hover {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  transform: translateX(2px);
}

/* 반응형 */
@media (max-width: 768px) {
  .mypage {
    padding: 16px 12px;
  }

  .page-title {
    font-size: 24px;
  }

  .profile-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .profile-score {
    align-items: flex-start;
  }

  .profile-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .products-grid {
    grid-template-columns: 1fr;
  }
}
</style>
