<template>
  <StocksMarketTab>
    <section class="stocks-home">
      <header class="stocks-header">
        <h1 class="title">국내 주식</h1>
        <p class="sub">한국 주식 데이터를 한 눈에 확인해보세요</p>
      </header>

      <!-- ✅ KRX 대시보드 -->
      <StocksMarketDashboard />

      <header class="stocks-header">
        <h1 class="title">주식 검색</h1>
        <p class="sub">관심있는 종목을 검색하고 궁금한 점을 챗봇에 질문해보세요</p>
      </header>

      <div class="card">
        <div class="search-row">
          <input
            v-model="store.searchQuery"
            class="search-input"
            placeholder="종목명 또는 코드 (예: 삼성 / 005930)"
            @keyup.enter="store.searchStocks"
          />
          <button class="btn" @click="store.searchStocks">검색</button>
        </div>

        <div v-if="store.error" class="error">{{ store.error }}</div>

        <ul v-if="store.searchResults.length" class="result-list">
          <li
            v-for="s in store.searchResults"
            :key="s.code"
            class="result-item"
          >
            <div class="left">
              <div class="name">{{ s.name }}</div>
              <div class="meta">{{ s.code }} <span v-if="s.market">· {{ s.market }}</span></div>
            </div>

            <RouterLink class="link" :to="{ name: 'stock_detail', params: { code: s.code } }">
              상세보기 →
            </RouterLink>
          </li>
        </ul>

        <div v-else class="empty">
          검색 결과가 없으면 아래 추천 리스트를 확인해보세요.
        </div>
      </div>

      <div class="card">
        <h2 class="card-title">오늘의 추천</h2>

        <div v-if="store.reco.detail" class="hint">{{ store.reco.detail }}</div>

        <ul class="reco-list">
          <li v-for="r in store.reco.recommendations.slice(0, 5)" :key="r.code" class="reco-item">
            <div class="left">
              <div class="name">{{ r.name }}</div>
              <div class="meta">{{ r.code }} · score {{ r.score }}</div>
            </div>

            <RouterLink class="link" :to="{ name: 'stock_detail', params: { code: r.code } }">
              보기 →
            </RouterLink>
          </li>
        </ul>

        <div v-if="!store.reco.count" class="empty">
          추천 데이터가 없습니다.
        </div>
      </div>
    </section>
  </StocksMarketTab>
</template>

<script setup>
import { onMounted } from "vue"
import { useStocksStore } from "@/stores/stocks"
import StocksMarketDashboard from "@/components/stocks/StocksMarketDashboard.vue"
import StocksMarketTab from "@/components/stocks/StocksMarketTab.vue"

const store = useStocksStore()

onMounted(() => {
  store.fetchRecommendations({ top: 5, auto: 1, include_news: 1 })
})
</script>

<style scoped>
.stocks-home { max-width: 980px; margin: 0 auto; }
.stocks-header { margin-bottom: 14px; }
.title { font-size: 28px; font-weight: 800; }
.sub { opacity: 0.7; margin-top: 6px; }

.card { background: rgba(255,255,255,0.85); border-radius: 14px; padding: 16px; margin-bottom: 14px; }
.search-row { display: flex; gap: 10px; align-items: center; }
.search-input { flex: 1; padding: 12px 12px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.12); }
.btn { padding: 12px 14px; border-radius: 10px; border: none; cursor: pointer; background: #2563eb; color: white; font-weight: 700; }
.row-between { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.card-title { font-size: 18px; font-weight: 800; }
.error { margin-top: 10px; color: #b00020; }
.hint { margin: 10px 0; opacity: 0.75; }

.result-list, .reco-list { list-style: none; padding: 0; margin: 12px 0 0; }
.result-item, .reco-item { display: flex; justify-content: space-between; align-items: center; padding: 12px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.08); margin-bottom: 10px; }
.name { font-weight: 800; }
.meta { opacity: 0.7; font-size: 13px; margin-top: 4px; }
.link { text-decoration: none; font-weight: 800; color: #2563eb; }
.empty { margin-top: 10px; opacity: 0.75; }
</style>
