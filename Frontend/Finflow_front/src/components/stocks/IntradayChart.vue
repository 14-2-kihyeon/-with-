<template>
  <div class="intraday-chart-container">
    <!-- 차트 컨트롤 -->
    <div class="chart-controls">
      <div class="interval-selector">
        <button
          v-for="int in intervals"
          :key="int.value"
          :class="['interval-btn', { active: interval === int.value }]"
          @click="changeInterval(int.value)"
        >
          {{ int.label }}
        </button>
      </div>

      <div class="days-selector">
        <button
          v-for="d in dayOptions"
          :key="d.value"
          :class="['days-btn', { active: days === d.value }]"
          @click="changeDays(d.value)"
        >
          {{ d.label }}
        </button>
      </div>
    </div>

    <!-- 차트 영역 -->
    <div class="chart-wrapper">
      <canvas ref="canvasEl"></canvas>

      <div v-if="loading" class="chart-loading overlay">
        <div class="spinner"></div>
        <p>차트 로딩 중...</p>
      </div>

      <div v-else-if="error" class="chart-error overlay">
        <p>{{ error }}</p>
        <button @click="refresh" class="btn-retry">재시도</button>
      </div>

      <div v-else-if="!prices.length" class="chart-empty overlay">
        <p>차트 데이터가 없습니다.</p>
      </div>
    </div>

    <!-- 차트 정보 -->
    <div v-if="!loading && !error && prices.length" class="chart-info">
      <span>데이터 개수: {{ prices.length }}개</span>
      <span>마지막 업데이트: {{ lastUpdate }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { apiGetIntradayPrices } from '@/api/stocks'
import axios from "axios"
import Chart from 'chart.js/auto'

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
    default: 60000 // 1분
  },
  isInternational: {
    type: Boolean,
    default: false
  }
})

// 상태
const canvasEl = ref(null)
const prices = ref([])
const loading = ref(false)
const error = ref(null)
const interval = ref('5m')
const days = ref(1)
const lastUpdate = ref('')
let chart = null
let refreshTimer = null

// 옵션
const intervals = [
  { label: '1분', value: '1m' },
  { label: '5분', value: '5m' },
  { label: '15분', value: '15m' },
  { label: '30분', value: '30m' },
  { label: '1시간', value: '1h' }
]

const dayOptions = [
  { label: '1일', value: 1 },
  { label: '5일', value: 5 },
]

// 인트라데이 데이터 조회
const fetchIntradayData = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await apiGetIntradayPrices(props.code, {
      interval: interval.value,
      days: days.value,
    })

    // ✅ 여기서가 제일 정확함 (요청 성공/실패와 무관)
    console.log(
      "[IntradayChart] request =",
      (response.config?.baseURL || "") + (response.config?.url || "")
    )
    console.log("[IntradayChart] Response:", response.data)

    const payload = response.data

    // ✅ 어떤 키로 와도 최대한 배열을 찾아서 prices로 세팅
    const extracted =
      payload.prices ??
      payload.data?.prices ??
      payload.data ??
      payload.results ??
      payload.items ??
      payload.intraday_prices ??
      []

    prices.value = Array.isArray(extracted) ? extracted : []
    lastUpdate.value = new Date().toLocaleTimeString('ko-KR')
    console.log('[IntradayChart] prices length =', prices.value.length)
    console.log('[IntradayChart] first row =', prices.value[0])

    // ✅ canvas/DOM 반영 후 렌더
    await nextTick()
    renderChart()

  } catch (e) {
    // ✅ Axios 에러 vs 일반 JS 에러 분리
    if (axios.isAxiosError(e)) {
      console.error("[IntradayChart] AxiosError:", e.message)
      console.error(
        "[IntradayChart] axios url =",
        (e.config?.baseURL || "") + (e.config?.url || "")
      )
      console.error("[IntradayChart] status =", e.response?.status)
      console.error("[IntradayChart] response =", e.response?.data)
      error.value = `차트 데이터 조회 오류: ${e.response?.status || ""} ${e.message}`
    } else {
      console.error("[IntradayChart] Non-Axios error:", e)
      error.value = `차트 렌더링/처리 중 오류: ${e?.message ?? e}`
    }

    prices.value = []
  } finally {
    loading.value = false
  }
}

// 차트 렌더링
const renderChart = () => {
  try {
    if (!canvasEl.value || !prices.value.length) return

    const ctx = canvasEl.value.getContext("2d")
    if (!ctx) throw new Error("canvas 2d context is null")

    if (chart) {
      chart.destroy()
      chart = null
    }

    const rows = prices.value
      .filter(p => p && p.datetime && p.close != null)
      .map(p => ({
        datetime: String(p.datetime),
        close: Number(p.close),
        volume: Number(p.volume ?? 0),
      }))

    if (!rows.length) return

    const labels = rows.map(p => {
      const dt = new Date(p.datetime.replace(' ', 'T'))
      return dt.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
    })

    const data = rows.map(p => Number(p.close))
    const volumes = rows.map(p => Number(p.volume ?? 0))
  // 차트 생성
  chart = new Chart(canvasEl.value.getContext('2d'), {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: '종가',
          data,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
          borderWidth: 2,
          tension: 0.1,
          fill: true,
          yAxisID: 'y',
        },
        {
          label: '거래량',
          data: volumes,
          type: 'bar',
          backgroundColor: 'rgba(156, 163, 175, 0.5)',
          borderColor: 'rgba(156, 163, 175, 0.8)',
          borderWidth: 1,
          yAxisID: 'y1',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || ''
              if (label) {
                label += ': '
              }
              if (context.datasetIndex === 0) {
                // 가격
                if (props.isInternational) {
                  label += '$' + context.parsed.y.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                } else {
                  label += context.parsed.y.toLocaleString('ko-KR') + '원'
                }
              } else {
                // 거래량
                label += context.parsed.y.toLocaleString('ko-KR')
              }
              return label
            }
          }
        }
      },
      scales: {
        x: {
          ticks: {
            maxTicksLimit: 10
          }
        },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: {
            display: true,
            text: props.isInternational ? '가격 (USD)' : '가격 (원)'
          },
          ticks: {
            callback: function(value) {
              if (props.isInternational) {
                return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
              }
              return value.toLocaleString('ko-KR')
            }
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: {
            display: true,
            text: '거래량'
          },
          grid: {
            drawOnChartArea: false
          },
          ticks: {
            callback: function(value) {
              if (value >= 1000000) {
                return (value / 1000000).toFixed(1) + 'M'
              } else if (value >= 1000) {
                return (value / 1000).toFixed(1) + 'K'
              }
              return value.toLocaleString('ko-KR')
            }
          }
        }
      }
    }
  })
  } catch (e) {
    console.error("[IntradayChart] renderChart error:", e)
    error.value = `차트 렌더링 오류: ${e.message}`
  }
}

// Interval 변경
const changeInterval = (newInterval) => {
  interval.value = newInterval
  fetchIntradayData()
}

// Days 변경
const changeDays = (newDays) => {
  days.value = newDays
  fetchIntradayData()
}

// 새로고침
const refresh = () => {
  fetchIntradayData()
}

// 자동 새로고침
const setupAutoRefresh = () => {
  if (props.autoRefresh) {
    refreshTimer = setInterval(() => {
      fetchIntradayData()
    }, props.refreshInterval)
  }
}

const clearAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// prices 변경 시 차트 재렌더링
watch(
  () => prices.value,
  () => {
    renderChart()
  },
  { deep: true }
)

onMounted(() => {
  fetchIntradayData().then(() => {
    setupAutoRefresh()
  })
})

onBeforeUnmount(() => {
  clearAutoRefresh()
  if (chart) {
    chart.destroy()
  }
})

// 외부에서 사용할 수 있도록 노출
defineExpose({
  refresh,
  fetchIntradayData
})
</script>

<style scoped>
.intraday-chart-container {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.interval-selector,
.days-selector {
  display: flex;
  gap: 8px;
}

.interval-btn,
.days-btn {
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
}

.interval-btn:hover,
.days-btn:hover {
  background: #f3f4f6;
}

.interval-btn.active,
.days-btn.active {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
}

.chart-wrapper { position: relative; height: 400px; min-height: 300px; }
.chart-wrapper canvas { width: 100% !important; height: 100% !important; }

.overlay{
  position: absolute;
  inset: 0;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  background: rgba(255,255,255,0.75);
}

.chart-loading,
.chart-error,
.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6b7280;
}

.spinner {
  border: 4px solid #f3f4f6;
  border-top: 4px solid #2563eb;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.chart-error {
  color: #ef4444;
}

.btn-retry {
  margin-top: 12px;
  padding: 8px 16px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-retry:hover {
  background: #1d4ed8;
}

.chart-info {
  display: flex;
  justify-content: space-between;
  margin-top: 16px;
  font-size: 12px;
  color: #6b7280;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

@media (max-width: 768px) {
  .chart-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .interval-selector,
  .days-selector {
    justify-content: center;
    flex-wrap: wrap;
  }

  .interval-btn,
  .days-btn {
    flex: 1;
    min-width: 60px;
  }



  .chart-info {
    flex-direction: column;
    gap: 4px;
  }
}
</style>
