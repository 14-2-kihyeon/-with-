<template>
  <div class="realtime-price-card">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>실시간 주가 로딩 중...</p>
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="refresh" class="btn-refresh">재시도</button>
    </div>

    <div v-else-if="data" class="price-content">
      <!-- 현재가 -->
      <div class="main-price">
        <div class="price-label">현재가</div>
        <div class="price-value" :class="priceChangeClass">
          {{ formatPrice(data.current_price) }}
        </div>
      </div>

      <!-- 등락 정보 -->
      <div class="price-change" :class="priceChangeClass">
        <span class="change-value">{{ formatChange(data.change) }}</span>
        <span class="change-percent">({{ formatPercent(data.change_percent) }}%)</span>
      </div>

      <!-- 상세 정보 -->
      <div class="price-details">
        <div class="detail-row">
          <span class="label">시가</span>
          <span class="value">{{ formatPrice(data.open) }}</span>
        </div>
        <div class="detail-row">
          <span class="label">고가</span>
          <span class="value high">{{ formatPrice(data.high) }}</span>
        </div>
        <div class="detail-row">
          <span class="label">저가</span>
          <span class="value low">{{ formatPrice(data.low) }}</span>
        </div>
        <div class="detail-row">
          <span class="label">전일</span>
          <span class="value">{{ formatPrice(data.previous_close) }}</span>
        </div>
        <div class="detail-row">
          <span class="label">거래량</span>
          <span class="value">{{ formatVolume(data.volume) }}</span>
        </div>
      </div>

      <!-- 시장 상태 -->
      <div class="market-status" :class="marketStatusClass">
        <span class="status-dot"></span>
        <span class="status-text">{{ marketStatusText }}</span>
        <span class="update-time">{{ data.updated_at }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { apiGetRealtimePrice } from '@/api/stocks'

const props = defineProps({
  code: {
    type: String,
    required: true
  },
  autoRefresh: {
    type: Boolean,
    default: true
  },
  refreshInterval: {
    type: Number,
    default: 60000 // 1분 (밀리초)
  },
  isInternational: {
    type: Boolean,
    default: false
  }
})

const data = ref(null)
const marketStatus = ref(null)
const loading = ref(false)
const error = ref(null)
let refreshTimer = null

// 실시간 주가 조회
const fetchRealtimePrice = async () => {
  loading.value = true
  error.value = null

  try {
    console.log('[RealtimePrice] Fetching for code:', props.code)
    const response = await apiGetRealtimePrice(props.code)
    console.log('[RealtimePrice] Response:', response.data)

    if (response.data.error) {
      console.error('[RealtimePrice] API Error:', response.data.detail)
      error.value = response.data.detail || '실시간 주가를 가져올 수 없습니다.'
      data.value = null
      marketStatus.value = null
    } else {
      data.value = response.data.data
      const payload = response.data
      data.value = payload.data ?? payload      // 둘 중 있는 걸로
      marketStatus.value = payload.market_status ?? null
      console.log('[RealtimePrice] Data loaded:', data.value)
    }
  } catch (e) {
    console.error('[RealtimePrice] Error fetching realtime price:', e)
    console.error('[RealtimePrice] Error details:', e.response?.data)
    error.value = `실시간 주가 조회 중 오류가 발생했습니다: ${e.message}`
    data.value = null
    marketStatus.value = null
  } finally {
    loading.value = false
  }
}

// 새로고침
const refresh = () => {
  fetchRealtimePrice()
}

// 가격 변동 클래스
const priceChangeClass = computed(() => {
  if (!data.value) return ''
  if (data.value.change > 0) return 'positive'
  if (data.value.change < 0) return 'negative'
  return 'neutral'
})

// 시장 상태 클래스
const marketStatusClass = computed(() => {
  if (!marketStatus.value) return ''
  return marketStatus.value.is_open ? 'open' : 'closed'
})

// 시장 상태 텍스트
const marketStatusText = computed(() => {
  if (!marketStatus.value) return ''

  if (marketStatus.value.is_open) {
    return '장중'
  } else {
    const nextOpen = marketStatus.value.next_open
    if (nextOpen) {
      return `장마감 (다음 개장: ${nextOpen.split(' ')[0]})`
    }
    return '장마감'
  }
})

// 포맷 함수들
const formatPrice = (price) => {
  if (!price) return '-'
  console.log('[RealtimePrice] formatPrice - isInternational:', props.isInternational, 'price:', price)
  if (props.isInternational) {
    return '$' + price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }
  return price.toLocaleString('ko-KR') + '원'
}

const formatChange = (change) => {
  if (!change) return props.isInternational ? '$0.00' : '0원'
  const sign = change > 0 ? '+' : ''
  if (props.isInternational) {
    return sign + '$' + Math.abs(change).toFixed(2)
  }
  return sign + change.toLocaleString('ko-KR') + '원'
}

const formatPercent = (percent) => {
  if (!percent) return '0.00'
  const sign = percent > 0 ? '+' : ''
  return sign + percent.toFixed(2)
}

const formatVolume = (volume) => {
  if (!volume) return '-'
  if (volume >= 1000000) {
    return (volume / 1000000).toFixed(1) + 'M'
  } else if (volume >= 1000) {
    return (volume / 1000).toFixed(1) + 'K'
  }
  return volume.toLocaleString('ko-KR')
}

// 자동 새로고침 설정
const setupAutoRefresh = () => {
  if (props.autoRefresh && marketStatus.value?.is_open) {
    refreshTimer = setInterval(() => {
      fetchRealtimePrice()
    }, props.refreshInterval)
  }
}

// 자동 새로고침 정리
const clearAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  fetchRealtimePrice().then(() => {
    setupAutoRefresh()
  })
})

onBeforeUnmount(() => {
  clearAutoRefresh()
})

// 외부에서 새로고침할 수 있도록 노출
defineExpose({
  refresh,
  fetchRealtimePrice
})
</script>

<style scoped>
.realtime-price-card {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 16px;
  padding: 24px;
  color: #1f2937;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-height: 280px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.loading {
  text-align: center;
  padding: 40px 0;
}

.spinner {
  border: 4px solid #f3f4f6;
  border-top: 4px solid #2563eb;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  text-align: center;
  color: #ef4444;
}

.btn-refresh {
  margin-top: 12px;
  padding: 8px 16px;
  background: #2563eb;
  border: 1px solid #2563eb;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-refresh:hover {
  background: #1d4ed8;
}

.price-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.main-price {
  text-align: center;
}

.price-label {
  font-size: 14px;
  opacity: 0.7;
  margin-bottom: 8px;
  color: #6b7280;
}

.price-value {
  font-size: 42px;
  font-weight: bold;
  letter-spacing: -1px;
  color: #1f2937;
}

.price-change {
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  gap: 8px;
  justify-content: center;
  align-items: center;
}

.positive {
  color: #ff4d4d;
}

.negative {
  color: #4d9eff;
}

.neutral {
  color: #6b7280;
}

.price-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 16px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.detail-row .label {
  opacity: 0.8;
}

.detail-row .value {
  font-weight: 600;
}

.detail-row .value.high {
  color: #ff6b6b;
}

.detail-row .value.low {
  color: #6bb6ff;
}

.market-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  opacity: 0.9;
  margin-top: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.market-status.open .status-dot {
  background: #4ade80;
  animation: pulse 2s infinite;
}

.market-status.closed .status-dot {
  background: #94a3b8;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.update-time {
  margin-left: auto;
  font-size: 11px;
  opacity: 0.7;
}

@media (max-width: 768px) {
  .realtime-price-card {
    padding: 16px;
  }

  .price-value {
    font-size: 32px;
  }

  .price-change {
    font-size: 16px;
  }

  .price-details {
    grid-template-columns: 1fr;
  }
}
</style>
