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
          <div class="btns">
            <button class="btn ghost" @click="reloadNews">불러오기</button>
            <button class="btn" @click="refreshNews">강제 갱신</button>
          </div>
        </div>

        <p class="small" v-if="store.news?.news_fetch">
          fetch: {{ store.news.news_fetch.reason }} / saved: {{ store.news.news_fetch.saved }}
        </p>

        <StockNewsList :items="store.news.items" />
      </div>

      <div class="card full">
        <div class="row-between">
          <h2 class="card-title">AI 설명</h2>
          <button class="btn" @click="ask">질문하기</button>
        </div>

        <textarea
          v-model="question"
          class="textarea"
          placeholder="예: 왜 이 종목이 추천됐어? 최근 뉴스 흐름은 어때?"
        />

        <div class="answer" v-if="store.explain?.answer">
          {{ store.explain.answer }}
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
import { onMounted, ref } from "vue"
import { useRoute } from "vue-router"
import { useStocksStore } from "@/stores/stocks"
import StockChart from "@/components/stocks/StockChart.vue"
import StockNewsList from "@/components/stocks/StockNewsList.vue"

const route = useRoute()
const store = useStocksStore()
const question = ref("왜 이 종목이 추천됐어?")

const code = route.params.code

const reloadAll = async () => {
  await store.fetchStockDetail(code, { auto: 1 })
  await store.fetchStockPrices(code) // 전체 1500개까지
  await store.fetchStockNews(code, { days: 7, limit: 10, refresh: 0 })
}

const reloadPrices = async () => {
  await store.fetchStockPrices(code)
}

const reloadNews = async () => {
  await store.fetchStockNews(code, { days: 7, limit: 10, refresh: 0 })
}

const refreshNews = async () => {
  await store.fetchStockNews(code, { days: 7, limit: 10, refresh: 1 })
}

const ask = async () => {
  await store.askExplain(code, {
    question: question.value,
    auto: 1,
    refresh_news: 1, // ✅ 뉴스 없으면 자동 저장까지 시도
  })
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

.textarea { width: 100%; min-height: 90px; margin-top: 12px; padding: 12px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.12); }
.answer { margin-top: 14px; padding: 12px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.08); background: rgba(255,255,255,0.65); line-height: 1.6; }

@media (max-width: 900px) {
  .grid { grid-template-columns: 1fr; }
}
</style>
