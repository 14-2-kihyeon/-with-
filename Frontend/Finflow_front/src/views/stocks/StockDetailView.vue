<template>
  <section class="stock-detail">
    <div class="top">
      <RouterLink class="back" :to="{ name: 'stocks_home' }">← 주식 홈</RouterLink>

      <div v-if="store.detail" class="title-wrap">
        <h1 class="title">{{ store.detail.name }}</h1>
        <p class="sub">{{ store.detail.code }} <span v-if="store.detail.market">· {{ store.detail.market }}</span></p>
        <p class="small">
          요청일: {{ store.detail.requested_as_of }} / 사용일: {{ store.detail.as_of_used }}
        </p>
        <p v-if="store.detail.detail" class="hint">{{ store.detail.detail }}</p>
      </div>

      <div v-if="store.error" class="error">{{ store.error }}</div>
    </div>

    <div class="grid">
      <div class="card">
        <div class="row-between">
          <h2 class="card-title">가격 차트</h2>
          <button class="btn ghost" @click="reloadPrices">새로고침</button>
        </div>
        <StockChart :prices="store.prices" />
      </div>

      <div class="card">
        <div class="row-between">
          <h2 class="card-title">뉴스</h2>
          <div class="pagination-btns" v-if="totalNewsPages > 1">
            <button class="btn ghost" :disabled="currentNewsPage === 1" @click="prevNewsPage">이전</button>
            <span class="page-info">{{ currentNewsPage }} / {{ totalNewsPages }}</span>
            <button class="btn ghost" :disabled="currentNewsPage === totalNewsPages" @click="nextNewsPage">다음</button>
          </div>
        </div>

        <p class="small" v-if="store.news?.news_fetch">
          fetch: {{ store.news.news_fetch.reason }} / saved: {{ store.news.news_fetch.saved }}
        </p>

        <StockNewsList :items="paginatedNews" />
      </div>

      <div class="card full">
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

const route = useRoute()
const store = useStocksStore()
const question = ref("왜 이 종목이 추천됐어?")

const code = route.params.code

// 뉴스 페이지네이션
const currentNewsPage = ref(1)
const newsPerPage = 3

// AI 설명 타이핑 애니메이션
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
  await store.fetchStockDetail(code, { auto: 1 })
  await store.fetchStockPrices(code) // 전체 1500개까지
  await store.fetchStockNews(code, { days: 7, limit: 10, refresh: 0 })
  currentNewsPage.value = 1 // 뉴스 로드 시 첫 페이지로 리셋

  // 백그라운드에서 AI 설명 미리 로드
  await loadAiAnswerInBackground()
}

const reloadPrices = async () => {
  await store.fetchStockPrices(code)
}

const loadAiAnswerInBackground = async () => {
  try {
    await store.askExplain(code, {
      question: question.value,
      auto: 1,
      refresh_news: 1,
    })

    // AI 응답을 fullAnswer에 저장하고 준비 완료 상태로 변경
    fullAnswer.value = store.explain?.answer || ""
    aiAnswerReady.value = true
  } catch (e) {
    console.error("AI 설명 로드 실패:", e)
    aiAnswerReady.value = false
  }
}

const showAnswer = async () => {
  if (isTyping.value) return

  // AI 답변이 아직 준비되지 않았다면 로딩 메시지 표시
  if (!aiAnswerReady.value) {
    isLoadingAI.value = true
    // AI 답변이 준비될 때까지 대기
    while (!aiAnswerReady.value) {
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    isLoadingAI.value = false
  }

  // 답변 타이핑 애니메이션 시작
  displayedAnswer.value = ""
  isTyping.value = true

  const text = fullAnswer.value
  const typingSpeed = 20 // 밀리초 단위 (빠르게 타이핑)

  for (let i = 0; i < text.length; i++) {
    displayedAnswer.value += text[i]
    await new Promise(resolve => setTimeout(resolve, typingSpeed))
  }

  isTyping.value = false
}

onMounted(() => {
  reloadAll()
})
</script>

<style scoped>
.stock-detail { max-width: 1100px; margin: 0 auto; padding: 20px; }
.top { margin-bottom: 14px; }
.back { text-decoration: none; font-weight: 800; display: inline-block; margin-bottom: 10px; }
.title-wrap { background: rgba(255,255,255,0.65); border-radius: 14px; padding: 14px; }
.title { font-size: 26px; font-weight: 900; margin: 0; }
.sub { opacity: 0.75; margin: 6px 0 0; }
.small { opacity: 0.7; font-size: 13px; margin-top: 8px; }
.hint { margin-top: 8px; opacity: 0.8; }
.error { color: #b00020; margin-top: 10px; }

.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.card { background: rgba(255,255,255,0.85); border-radius: 14px; padding: 16px; }
.card.full { grid-column: 1 / -1; }
.row-between { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.card-title { font-size: 18px; font-weight: 900; margin: 0; }
.btns { display: flex; gap: 8px; }

.btn { padding: 10px 12px; border-radius: 10px; border: none; cursor: pointer; }
.btn.ghost { background: transparent; border: 1px solid rgba(0,0,0,0.12); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.pagination-btns { display: flex; gap: 8px; align-items: center; }
.page-info { font-size: 13px; font-weight: 800; opacity: 0.7; }

.textarea { width: 100%; min-height: 90px; margin-top: 12px; padding: 12px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.12); font-size: 14px; }

.loading-message {
  margin-top: 14px;
  padding: 20px;
  border-radius: 14px;
  border: 1px solid rgba(37, 99, 235, 0.15);
  background: rgba(37, 99, 235, 0.05);
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: rgba(37, 99, 235, 0.95);
  font-weight: 600;
}

.loading-spinner-small {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 3px solid rgba(37, 99, 235, 0.15);
  border-top-color: rgba(37, 99, 235, 0.95);
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

.answer {
  margin-top: 14px;
  padding: 20px;
  border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.08);
  background: rgba(255,255,255,0.85);
  line-height: 1.8;
  white-space: pre-wrap;
  font-size: 15px;
  color: rgba(15, 23, 42, 0.95);
  word-break: keep-all;
  letter-spacing: 0.3px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.cursor {
  display: inline-block;
  margin-left: 2px;
  animation: blink 0.8s infinite;
  color: rgba(37, 99, 235, 0.8);
  font-weight: 900;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 900px) {
  .grid { grid-template-columns: 1fr; }
}
</style>
