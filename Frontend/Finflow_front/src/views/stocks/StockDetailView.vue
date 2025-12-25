<template>
  <section class="stock-detail">
    <div class="top">
      <RouterLink class="back" :to="backRoute">← {{ backLabel }}</RouterLink>

      <div v-if="stockInfo" class="title-wrap">
        <h1 class="title">{{ stockInfo.name }}</h1>
        <p class="sub">{{ code }} <span v-if="stockInfo.market">· {{ marketLabel }}</span></p>
        <p class="small" v-if="!isInternational">
          요청일: {{ stockInfo.requested_as_of }} / 사용일: {{ stockInfo.as_of_used }}
        </p>
        <p v-if="stockInfo.detail" class="hint">{{ stockInfo.detail }}</p>
      </div>

      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <div class="grid">
      <!-- 실시간 주가 카드 -->
      <div class="card realtime-card">
        <RealtimeStockPrice
          :code="code"
          :auto-refresh="true"
          :refresh-interval="60000"
          :is-international="isInternational"
          ref="realtimePriceRef"
        />
      </div>

      <!-- 인트라데이 차트 -->
      <div class="card intraday-card">
        <h2 class="card-title">실시간 차트 <span v-if="isInternational" class="unit-hint">(USD 기준)</span></h2>
        <IntradayChart
          :code="code"
          :auto-refresh="true"
          :refresh-interval="60000"
          :is-international="isInternational"
          ref="intradayChartRef"
        />
      </div>

      <!-- 일봉 차트 (국내 주식만) -->
      <div v-if="!isInternational" class="card daily-card">
        <div class="row-between">
          <h2 class="card-title">일봉 차트</h2>
          <button class="btn ghost" @click="reloadPrices">새로고침</button>
        </div>
        <StockChart :prices="store.prices" />
      </div>


      <!-- 뉴스 (국내 주식만) -->
      <div v-if="!isInternational" class="card news-card">
        <div class="row-between">
          <h2 class="card-title"> 📈 뉴스</h2>
          <div class="pagination-btns" v-if="totalNewsPages > 0">
            <button class="btn ghost" :disabled="currentNewsPage === 1" @click="prevNewsPage">이전</button>
            <span class="page-info">{{ currentNewsPage }} / {{ totalNewsPages }}</span>
            <button class="btn ghost" :disabled="currentNewsPage === totalNewsPages" @click="nextNewsPage">다음</button>
          </div>
        </div>

        <StockNewsList :items="paginatedNews" />
      </div>


      <!-- AI 설명 (국내 주식만) -->
      <div v-if="!isInternational" class="card full">
        <div class="row-between">
          <h2 class="card-title">AI 설명</h2>
          <button class="btn" @click="showAnswer" :disabled="isTyping">
            {{ isTyping ? '답변 중...' : '질문하기' }}
          </button>
        </div>

        <textarea
          v-model="question"
          class="textarea"
          placeholder="예: 왜 이 종목이 추천됐어? 최근 뉴스 흐름은 어때?"
        />

        <div class="loading-message" v-if="isLoadingAI">
          <div class="loading-spinner-small"></div>
          <span>AI가 답변을 준비하고 있습니다. 잠시만 기다려주세요...</span>
        </div>

        <div class="answer" v-if="displayedAnswer">
          {{ displayedAnswer }}
          <span v-if="isTyping" class="cursor">|</span>
        </div>

        <div class="small" v-if="store.explain?.used">
          feature: {{ store.explain.used.feature_available }} /
          news_count: {{ store.explain.used.news_count }} /
          news_fetch: {{ store.explain.used.news_fetch?.reason }}
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref, computed } from "vue"
import { useRoute } from "vue-router"
import { useStocksStore } from "@/stores/stocks"
import StockChart from "@/components/stocks/StockChart.vue"
import StockNewsList from "@/components/stocks/StockNewsList.vue"
import RealtimeStockPrice from "@/components/stocks/RealtimeStockPrice.vue"
import IntradayChart from "@/components/stocks/IntradayChart.vue"

const route = useRoute()
const store = useStocksStore()
const question = ref("왜 이 종목이 추천됐어?")

const code = route.params.code

// 종목 정보
const stockInfo = ref(null)
const error = ref(null)

// 실시간 주가 및 차트 컴포넌트 참조
const realtimePriceRef = ref(null)
const intradayChartRef = ref(null)

// 국제 시장 여부 판단 (미국 주식 또는 암호화폐)
const isInternational = computed(() => {
  // 코드에 하이픈이 있으면 암호화폐 (BTC-USD)
  if (code.includes('-')) {
    console.log('[StockDetail] isInternational = true (crypto):', code)
    return true
  }
  // 코드가 숫자로만 이루어져 있으면 국내 주식
  if (/^\d+$/.test(code)) {
    console.log('[StockDetail] isInternational = false (domestic):', code)
    return false
  }
  // 그 외는 미국 주식 (AAPL, TSLA 등)
  console.log('[StockDetail] isInternational = true (US stock):', code)
  return true
})

// 백 버튼 라벨 및 라우트
const backLabel = computed(() => {
  if (code.includes('-')) return '암호화폐 홈'
  if (/^\d+$/.test(code)) return '주식 홈'
  return '해외 주식 홈'
})

const backRoute = computed(() => {
  if (code.includes('-')) return { name: 'stocks_crypto' }
  if (/^\d+$/.test(code)) return { name: 'stocks_home' }
  return { name: 'stocks_global' }
})

// 시장 라벨
const marketLabel = computed(() => {
  if (code.includes('-')) return 'CRYPTO'
  if (/^\d+$/.test(code)) return stockInfo.value?.market || 'KOSPI'
  return 'US'
})

// 뉴스 페이지네이션 (국내 주식만)
const currentNewsPage = ref(1)
const newsPerPage = 1

// AI 설명 타이핑 애니메이션 (국내 주식만)
const isTyping = ref(false)
const isLoadingAI = ref(false)
const aiAnswerReady = ref(false)
const displayedAnswer = ref("")
const fullAnswer = ref("")

const totalNewsPages = computed(() => {
  const total = store.news?.items?.length || 0
  return Math.ceil(total / newsPerPage)
})

const paginatedNews = computed(() => {
  const items = store.news?.items || []
  const start = (currentNewsPage.value - 1) * newsPerPage
  const end = start + newsPerPage
  return items.slice(start, end)
})

const nextNewsPage = () => {
  if (currentNewsPage.value < totalNewsPages.value) {
    currentNewsPage.value++
  }
}

const prevNewsPage = () => {
  if (currentNewsPage.value > 1) {
    currentNewsPage.value--
  }
}

const reloadAll = async () => {
  if (isInternational.value) {
    // 해외 주식/암호화폐: 실시간 데이터만 로드
    await loadInternationalStock()
  } else {
    // 국내 주식: 모든 데이터 로드
    await store.fetchStockDetail(code, { auto: 1 })
    stockInfo.value = store.detail
    await store.fetchStockPrices(code)
    await store.fetchStockNews(code, { days: 7, limit: 10, refresh: 0 })
    currentNewsPage.value = 1
    await loadAiAnswerInBackground()
  }
}

const reloadPrices = async () => {
  await store.fetchStockPrices(code)
}

const loadInternationalStock = async () => {
  try {
    // 실시간 가격 API로 종목 이름 가져오기
    const response = await import('@/api/stocks').then(m => m.apiGetRealtimePrice(code))
    const data = response.data.data

    stockInfo.value = {
      name: data?.name || code,
      code: code,
      market: code.includes('-') ? 'CRYPTO' : 'US'
    }
    error.value = null
  } catch (e) {
    console.error('Failed to load stock info:', e)
    error.value = '종목 정보를 가져올 수 없습니다.'
    stockInfo.value = {
      name: code,
      code: code,
      market: code.includes('-') ? 'CRYPTO' : 'US'
    }
  }
}

const loadAiAnswerInBackground = async () => {
  try {
    await store.askExplain(code, {
      question: question.value,
      auto: 1,
      refresh_news: 1,
    })

    fullAnswer.value = store.explain?.answer || ""
    aiAnswerReady.value = true
  } catch (e) {
    console.error("AI 설명 로드 실패:", e)
    aiAnswerReady.value = false
  }
}

const showAnswer = async () => {
  if (isTyping.value) return

  if (!aiAnswerReady.value) {
    isLoadingAI.value = true
    while (!aiAnswerReady.value) {
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    isLoadingAI.value = false
  }

  if (!fullAnswer.value) {
    displayedAnswer.value = "AI 설명을 불러올 수 없습니다."
    return
  }

  displayedAnswer.value = ""
  isTyping.value = true

  let index = 0
  const text = fullAnswer.value
  const typingSpeed = 5

  const typeInterval = setInterval(() => {
    if (index < text.length) {
      displayedAnswer.value += text[index]
      index++
    } else {
      clearInterval(typeInterval)
      isTyping.value = false
    }
  }, typingSpeed)
}

onMounted(async () => {
  if (isInternational.value) {
    await loadInternationalStock()
  } else {
    await reloadAll()
  }
})
</script>

<style scoped>
.stock-detail {
  max-width: 1120px;
  margin: 0 auto;
  padding: 20px;
}

.top {
  margin-bottom: 20px;
}

.back {
  display: inline-block;
  margin-bottom: 10px;
  color: #2563eb;
  text-decoration: none;
  font-weight: 800;
  font-size: 14px;
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(37, 99, 235, 0.08);
  transition: all 0.3s;
}

.back:hover {
  background: rgba(37, 99, 235, 0.15);
}

.title-wrap {
  margin-top: 10px;
}

.title {
  font-size: 32px;
  font-weight: 900;
  margin: 0;
}

.sub {
  font-size: 14px;
  opacity: 0.7;
  margin-top: 8px;
}

.small {
  font-size: 12px;
  opacity: 0.6;
  margin-top: 6px;
}

.hint {
  font-size: 13px;
  opacity: 0.75;
  margin-top: 8px;
  padding: 10px;
  background: rgba(37, 99, 235, 0.05);
  border-radius: 8px;
}

.error {
  color: #ef4444;
  font-weight: 800;
  margin-top: 10px;
  padding: 12px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 10px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr)); /* ✅ 12칸 고정 */
  gap: 20px;
  align-items: start;
}

/* ✅ 큰 카드들은 전체 폭 */
.realtime-card,
.intraday-card,
.card.full {
  grid-column: 1 / -1;
}

.card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 14px;
  padding: 20px;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.realtime-card {
  grid-column: 1 / -1;
}

.intraday-card {
  grid-column: 1 / -1;
}

.card.full {
  grid-column: 1 / -1;
}

.card-title {
  font-size: 18px;
  font-weight: 800;
  margin: 0 0 16px 0;
}

.unit-hint {
  font-size: 13px;
  opacity: 0.6;
  font-weight: 600;
}

.row-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.btn {
  padding: 10px 16px;
  border-radius: 10px;
  border: none;
  background: #2563eb;
  color: white;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.3s;
}

.btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.ghost {
  background: rgba(0, 0, 0, 0.05);
  color: #333;
}

.btn.ghost:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.1);
}

.pagination-btns {
  display: flex;
  gap: 10px;
  align-items: center;
}

.page-info {
  font-size: 13px;
  font-weight: 700;
}

.textarea {
  width: 100%;
  min-height: 80px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  font-family: inherit;
  font-size: 14px;
  resize: vertical;
}

.loading-message {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  padding: 16px;
  background: rgba(37, 99, 235, 0.05);
  border-radius: 10px;
}

.loading-spinner-small {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(37, 99, 235, 0.2);
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.answer {
  margin-top: 16px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 10px;
  white-space: pre-wrap;
  line-height: 1.6;
}

.cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}

/* ✅ 일봉/뉴스가 한 줄을 2등분으로 꽉 채움 */
.daily-card {
  grid-column: span 6;
}

.news-card {
  grid-column: span 6;
}

/* ✅ 모바일/태블릿에서는 한 줄씩 */
@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
  .daily-card,
  .news-card,
  .realtime-card,
  .intraday-card,
  .card.full {
    grid-column: 1 / -1;
  }
}
</style>  