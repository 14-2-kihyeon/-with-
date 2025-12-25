<template>
  <div class="crypto-market-dashboard">
    <div class="dashboard-grid">
      <!-- 비트코인 차트 -->
      <div class="chart-card">
        <h3 class="chart-title">Bitcoin (BTC) - 최근 30일</h3>
        <div class="chart-placeholder">
          <canvas ref="btcChart"></canvas>
        </div>
      </div>

      <!-- 이더리움 차트 -->
      <div class="chart-card">
        <h3 class="chart-title">Ethereum (ETH) - 최근 30일</h3>
        <div class="chart-placeholder">
          <canvas ref="ethChart"></canvas>
        </div>
      </div>

      <!-- 환율 -->
      <div class="exchange-card">
        <div class="side-head">
          <div class="t1">환율</div>
        </div>

        <div class="muted small">기준: {{ fxDate }}</div>
        <div v-if="error" class="err">{{ error }}</div>

        <ul v-if="!loading && !error" class="fx-list">
          <li v-for="fx in exchangeRates" :key="fx.pair" class="fx-item">
            <div class="fx-left">
              <img v-if="flagSrc(fx.pair)" class="flag" :src="flagSrc(fx.pair)" alt="flag" />
              <div v-else class="flag ph"></div>

              <div class="fx-meta">
                <div class="pair">{{ fx.pair }}</div>
                <div class="date muted">{{ fx.date || '-' }}</div>
              </div>
            </div>

            <div class="fx-right">
              <div class="fx-row">
                <div class="rate">
                  {{ fx.rate }}
                  <span class="dot">•</span>
                  <span class="mini" :class="fx.changeClass">
                    {{ fx.arrow }} {{ fx.changeDelta }}
                  </span>
                </div>
              </div>

              <div class="fx-pct muted">
                {{ fx.changePct }}
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Chart from 'chart.js/auto'
import api from '@/api/axios'

import usFlag from '@/assets/flag/us.png'
import jpFlag from '@/assets/flag/jp.png'
import euFlag from '@/assets/flag/eu.png'
import cnFlag from '@/assets/flag/cn.png'

const btcChart = ref(null)
const ethChart = ref(null)
const exchangeRates = ref([])
const fxDate = ref('-')
const loading = ref(false)
const error = ref(null)

// 환율 국기 매핑
const flagMap = { 'USD/KRW': usFlag, 'JPY/KRW': jpFlag, 'EUR/KRW': euFlag, 'CNY/KRW': cnFlag }
function flagSrc(pair) { return flagMap[pair] || null }

// 포맷 함수들
function fmtFx(v) {
  const x = Number(v)
  if (!Number.isFinite(x)) return '-'
  return x.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function fmtFxDelta(n) {
  const x = Number(n)
  if (!Number.isFinite(x)) return '-'
  const s = x > 0 ? '+' : ''
  return `${s}${x.toFixed(2)}`
}

function fmtFxPct(v) {
  const x = Number(v)
  if (!Number.isFinite(x)) return '-'
  return (x > 0 ? `+${x.toFixed(2)}` : x.toFixed(2))
}

function arrow(v) {
  const x = Number(v)
  if (!Number.isFinite(x) || x === 0) return '•'
  return x > 0 ? '▲' : '▼'
}

function signClass(n) {
  const x = Number(n)
  if (Number.isNaN(x)) return ''
  if (x > 0) return 'up'
  if (x < 0) return 'dn'
  return ''
}

// 환율 데이터 가져오기
const fetchExchangeRates = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/stocks/market/fx/snapshot/')
    const data = response.data.items || []
    fxDate.value = response.data.as_of || '-'

    exchangeRates.value = data
      .filter(item => item.rate != null)
      .map(item => ({
        pair: item.pair,
        date: item.date || '-',
        rate: fmtFx(item.rate),
        changeDelta: fmtFxDelta(item.change),
        changePct: item.change_pct == null ? '-' : `(${fmtFxPct(item.change_pct)}%)`,
        arrow: arrow(item.change),
        changeClass: signClass(item.change)
      }))
  } catch (e) {
    console.error('Failed to fetch exchange rates:', e)
    error.value = '환율 데이터를 가져올 수 없습니다'
  } finally {
    loading.value = false
  }
}

// 실제 차트 데이터 가져오기
const createChartWithData = async (canvasRef, code, label, color) => {
  if (!canvasRef.value) return

  try {
    // 최근 30일 데이터 가져오기
    const response = await api.get(`/api/stocks/${code}/intraday/`, {
      params: {
        interval: '1d',
        days: 30
      }
    })

    const prices = response.data.prices || []

    if (!prices.length) {
      console.warn(`No data for ${code}`)
      return
    }

    const labels = prices.map(p => {
      const dt = new Date(p.datetime)
      return `${dt.getMonth() + 1}/${dt.getDate()}`
    })
    const data = prices.map(p => p.close)

    new Chart(canvasRef.value, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label,
          data,
          borderColor: color,
          backgroundColor: `${color}20`,
          borderWidth: 2,
          tension: 0.1,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: {
            display: true,
            ticks: {
              maxTicksLimit: 6
            }
          },
          y: {
            ticks: {
              callback: (value) => '$' + value.toLocaleString()
            }
          }
        }
      }
    })
  } catch (e) {
    console.error(`Failed to fetch data for ${code}:`, e)
  }
}

onMounted(() => {
  fetchExchangeRates()
  createChartWithData(btcChart, 'BTC-USD', 'BTC', '#f7931a')
  createChartWithData(ethChart, 'ETH-USD', 'ETH', '#627eea')
})
</script>

<style scoped>
.crypto-market-dashboard {
  margin-bottom: 20px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 14px;
}

.chart-card {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 14px;
  padding: 16px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.chart-title {
  font-size: 16px;
  font-weight: 800;
  margin: 0 0 12px 0;
}

.chart-placeholder {
  height: 280px;
  position: relative;
}

.exchange-card {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 14px;
  padding: 16px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.side-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.t1 {
  font-size: 16px;
  font-weight: 800;
}

.muted {
  opacity: 0.65;
}

.small {
  font-size: 12px;
  margin-bottom: 12px;
}

.err {
  margin-top: 10px;
  color: #b00020;
  font-weight: 800;
}

.fx-list {
  list-style: none;
  padding: 0;
  margin: 12px 0 0;
  display: grid;
  gap: 10px;
}

.fx-item {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.fx-left {
  display: flex;
  gap: 10px;
  align-items: center;
  min-width: 0;
}

.fx-meta {
  min-width: 0;
}

.flag {
  width: 28px;
  height: 20px;
  border-radius: 6px;
  object-fit: cover;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.flag.ph {
  width: 28px;
  height: 20px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.pair {
  font-weight: 900;
  font-size: 13px;
  white-space: nowrap;
}

.date {
  font-size: 12px;
  white-space: nowrap;
}

.fx-right {
  text-align: right;
  min-width: 120px;
}

.fx-row {
  display: flex;
  align-items: baseline;
  justify-content: flex-end;
  gap: 10px;
}

.rate {
  font-weight: 900;
}

.fx-pct {
  font-size: 12px;
  margin-top: 2px;
}

.dot {
  opacity: 0.35;
  margin: 0 6px;
}

.mini {
  font-weight: 900;
  font-size: 12px;
}

.up {
  color: #d10b2a;
}

.dn {
  color: #1e5eff;
}

@media (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>
