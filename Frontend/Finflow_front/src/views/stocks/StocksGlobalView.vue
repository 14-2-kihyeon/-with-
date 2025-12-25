<template>
  <StocksMarketTab>
    <section class="stocks-global">
      <header class="stocks-header">
        <h1 class="title">해외 주식</h1>
        <p class="sub">미국 주식 데이터를 한 눈에 확인해보세요</p>
      </header>

      <!-- 글로벌 대시보드 -->
      <GlobalMarketDashboard />

      <!-- Top 5 거래대금 -->
      <TopVolumeList
        title="🔥 실시간 거래대금 Top 5"
        :items="popularStocks"
        market="US"
      />
    </section>
  </StocksMarketTab>
</template>

<script setup>
import StocksMarketTab from '@/components/stocks/StocksMarketTab.vue'
import GlobalMarketDashboard from '@/components/stocks/GlobalMarketDashboard.vue'
import TopVolumeList from '@/components/stocks/TopVolumeList.vue'

// 인기 미국 주식
const popularStocks = [
  { code: 'AAPL', name: 'Apple Inc.' },
  { code: 'MSFT', name: 'Microsoft Corporation' },
  { code: 'GOOGL', name: 'Alphabet Inc.' },
  { code: 'AMZN', name: 'Amazon.com Inc.' },
  { code: 'NVDA', name: 'NVIDIA Corporation' },
  { code: 'TSLA', name: 'Tesla Inc.' },
  { code: 'META', name: 'Meta Platforms Inc.' },
  { code: 'BRK.B', name: 'Berkshire Hathaway Inc.' }
]
</script>

<style scoped>
.stocks-global { max-width: 980px; margin: 0 auto; }
.stocks-header { margin-bottom: 14px; }
.title { font-size: 28px; font-weight: 800; }
.sub { opacity: 0.7; margin-top: 6px; }
</style>
