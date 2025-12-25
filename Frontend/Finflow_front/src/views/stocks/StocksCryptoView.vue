<template>
  <StocksMarketTab>
    <section class="stocks-crypto">
      <header class="stocks-header">
        <h1 class="title">암호화폐</h1>
        <p class="sub">실시간 암호화폐 시세를 한 눈에 확인해보세요</p>
      </header>

      <!-- 암호화폐 대시보드 -->
      <CryptoMarketDashboard />

      <!-- Top 5 거래대금 -->
      <TopVolumeList
        title="💰 실시간 거래대금 Top 5"
        :items="majorCryptos"
        market="CRYPTO"
      />
    </section>
  </StocksMarketTab>
</template>

<script setup>
import StocksMarketTab from '@/components/stocks/StocksMarketTab.vue'
import CryptoMarketDashboard from '@/components/stocks/CryptoMarketDashboard.vue'
import TopVolumeList from '@/components/stocks/TopVolumeList.vue'

// 주요 암호화폐
const majorCryptos = [
  { code: 'BTC-USD', name: 'Bitcoin' },
  { code: 'ETH-USD', name: 'Ethereum' },
  { code: 'BNB-USD', name: 'Binance Coin' },
  { code: 'XRP-USD', name: 'Ripple' },
  { code: 'ADA-USD', name: 'Cardano' },
  { code: 'DOGE-USD', name: 'Dogecoin' },
  { code: 'SOL-USD', name: 'Solana' },
  { code: 'MATIC-USD', name: 'Polygon' }
]
</script>

<style scoped>
.stocks-crypto { max-width: 980px; margin: 0 auto; }
.stocks-header { margin-bottom: 14px; }
.title { font-size: 28px; font-weight: 800; }
.sub { opacity: 0.7; margin-top: 6px; }
</style>
