<template>
  <section class="krx-wrap">
    <!-- 로딩 오버레이 -->
    <div v-if="initialLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">시장 데이터를 불러오는 중...</div>
    </div>

    <!-- 메인 컨텐츠 -->
    <div v-show="!initialLoading" class="krx-grid">
      <!-- 좌: 차트 -->
      <div class="krx-card krx-main">
        <div class="krx-head">
          <div class="krx-title">
            <div class="t1">{{ selectedLabel }}</div>
            <div class="t2">
              <span v-if="latestPoint">
                {{ fmt(latestPoint.close) }}
                <span class="chg">( {{ interval.toUpperCase() }} / {{ range.toUpperCase() }} )</span>
              </span>
              <span v-else class="muted">데이터 없음</span>
            </div>
          </div>

          <div class="krx-controls">
            <div class="btn-group">
              <button class="btn" :class="{ on: symbol==='KS11' }" @click="setSymbol('KS11','KOSPI')">KOSPI</button>
              <button class="btn" :class="{ on: symbol==='KQ11' }" @click="setSymbol('KQ11','KOSDAQ')">KOSDAQ</button>
              <button class="btn" :class="{ on: symbol==='KS200' }" @click="setSymbol('KS200','KOSPI200')">KOSPI200</button>
            </div>

            <div class="btn-group">
              <button class="btn" :class="{ on: interval==='day' }" @click="interval='day'">Day</button>
              <button class="btn" :class="{ on: interval==='week' }" @click="interval='week'">Week</button>
            </div>

            <div class="btn-group">
              <button class="btn" :class="{ on: range==='3m' }" @click="range='3m'">3M</button>
              <button class="btn" :class="{ on: range==='6m' }" @click="range='6m'">6M</button>
              <button class="btn" :class="{ on: range==='1y' }" @click="range='1y'">1Y</button>
              <button class="btn" :class="{ on: range==='5y' }" @click="range='5y'">5Y</button>
              <button class="btn" :class="{ on: range==='all' }" @click="range='all'">ALL</button>
            </div>
          </div>
        </div>

        <div class="krx-chart">
          <canvas ref="canvasEl"></canvas>
        </div>

        <div class="krx-foot">
          <span class="muted">기준일:</span>
          <span>{{ (marketStore.summary?.requested_as_of || marketStore.fx?.as_of || '-') }}</span>
        </div>
      </div>

      <!-- 우: 환율 -->
      <div class="krx-card krx-side">
        <div class="side-head">
          <div class="t1">환율</div>
          <button class="refresh" :class="{ loading: fxRefreshing }" :disabled="fxRefreshing" @click="refreshFx">
            <span class="ico" aria-hidden="true">↻</span>
            새로고침
          </button>
        </div>

        <div class="muted small">기준: {{ marketStore.fx?.as_of || '-' }}</div>
        <div v-if="marketStore.error" class="err">{{ marketStore.error }}</div>

        <ul class="fx-list">
          <li v-for="it in (marketStore.fx?.items || [])" :key="it.pair || it.symbol" class="fx-item">
            <div class="fx-left">
              <img v-if="flagSrc(it.pair || it.symbol)" class="flag" :src="flagSrc(it.pair || it.symbol)" alt="flag" />
              <div v-else class="flag ph"></div>

              <div class="fx-meta">
                <div class="pair">{{ it.pair || it.symbol }}</div>
                <div class="date muted">{{ it.date || '-' }}</div>
              </div>
            </div>

            <div class="fx-right">
              <!-- ✅ 값 + 변동폭(옆에) -->
              <div class="fx-row">
                <div class="rate">
                {{ fmtFx(it.rate ?? it.value ?? it.close) }}
                <span class="dot">•</span>
                <span class="mini" :class="signClass(it.change)">
                    {{ arrow(it.change) }} {{ fmtFxDelta(it.change) }}
                </span>
                </div>
              </div>

              <!-- (선택) 퍼센트는 아래에 작게 -->
              <div class="fx-pct muted">
                {{ it.change_pct == null ? "-" : `(${fmtFxPct(it.change_pct)}%)` }}
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <!-- 시장 요약 -->
    <div v-show="!initialLoading" class="krx-card krx-summary">
      <div class="sum-head">
        <div class="t1">시장 요약</div>

        <div class="sum-tabs">
          <button class="tab" :class="{ on: summaryMarket==='ALL' }" @click="summaryMarket='ALL'">ALL</button>
          <button class="tab" :class="{ on: summaryMarket==='KOSPI' }" @click="summaryMarket='KOSPI'">KOSPI</button>
          <button class="tab" :class="{ on: summaryMarket==='KOSDAQ' }" @click="summaryMarket='KOSDAQ'">KOSDAQ</button>
        </div>

        <button class="refresh" :class="{ loading: sumRefreshing }" :disabled="sumRefreshing" @click="refreshSummary">
          <span class="ico" aria-hidden="true">↻</span>
          새로고침
        </button>
      </div>

      <div class="muted small">기준: {{ marketStore.summary?.as_of_used || '-' }}</div>

      <div class="sum-grid sum-grid-3">
        <div class="sum-card">
          <div class="sum-title">거래 규모</div>
          <div class="sum-row"><span class="k">거래량</span><span class="v">{{ fmtCompact(turnover.volume, "주") }}</span></div>
          <div class="sum-row"><span class="k">거래대금</span><span class="v">{{ fmtWonCompact(turnover.amount) }}</span></div>
          <div class="muted small mt8">* 거래대금은 원화(₩) 기준</div>
        </div>

        <div class="sum-card">
          <div class="sum-title">상승 Top 5</div>
          <div v-if="!topGainers.length" class="muted small">데이터 없음</div>
          <div v-for="it in topGainers" :key="it.code" class="top-row">
            <span class="code">{{ it.code }}</span>
            <span class="name" :title="it.name">{{ it.name }}</span>
            <!-- ✅ r1은 '수익률(비율)'로 보고 무조건 *100 -->
            <span class="pct up">{{ fmtSigned(toPct(it.r1)) }}%</span>
          </div>
        </div>

        <div class="sum-card">
          <div class="sum-title">하락 Top 5</div>
          <div v-if="!topLosers.length" class="muted small">데이터 없음</div>
          <div v-for="it in topLosers" :key="it.code" class="top-row">
            <span class="code">{{ it.code }}</span>
            <span class="name" :title="it.name">{{ it.name }}</span>
            <span class="pct dn">{{ fmtSigned(toPct(it.r1)) }}%</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"
import Chart from "chart.js/auto"
import { useMarketStore } from "@/stores/market"

import usFlag from "@/assets/flag/us.png"
import jpFlag from "@/assets/flag/jp.png"
import euFlag from "@/assets/flag/eu.png"
import cnFlag from "@/assets/flag/cn.png"

const marketStore = useMarketStore()

const canvasEl = ref(null)
let chart = null

const symbol = ref("KS11")
const selectedLabel = ref("KOSPI")
const interval = ref("day")
const range = ref("all")
const summaryMarket = ref("ALL")
const initialLoading = ref(true) // 최초 로딩 상태

function setSymbol(sym, label) {
  symbol.value = sym
  selectedLabel.value = label
}

// ---------- 새로 고침 ----------
const fxRefreshing = ref(false)
const sumRefreshing = ref(false)
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function refreshFx() {
  if (fxRefreshing.value) return
  fxRefreshing.value = true
  try {
    await marketStore.fetchFx()
    await sleep(450)
  } finally {
    fxRefreshing.value = false
  }
}

async function refreshSummary() {
  if (sumRefreshing.value) return
  sumRefreshing.value = true
  try {
    await marketStore.fetchMarketSummary(summaryMarket.value)
    await sleep(450)
  } finally {
    sumRefreshing.value = false
  }
}

// ✅ 핵심 수정: r1은 "비율"로 보고 항상 *100 (2.06 -> 206%)
function toPct(r1) {
  const x = Number(r1)
  if (!Number.isFinite(x)) return null
  return x * 100
}

// ---------- 날짜 유틸 ----------
function parseDate(s) {
  if (!s) return null
  if (s instanceof Date) return s
  const parts = String(s).split("-").map(Number)
  if (parts.length !== 3) return null
  const [y, m, d] = parts
  if (!y || !m || !d) return null
  return new Date(y, m - 1, d)
}

function subtractRange(lastDateStr) {
  if (range.value === "all") return null
  const last = parseDate(lastDateStr)
  if (!last) return null

  const d = new Date(last)
  if (range.value === "3m") d.setMonth(d.getMonth() - 3)
  else if (range.value === "6m") d.setMonth(d.getMonth() - 6)
  else if (range.value === "1y") d.setFullYear(d.getFullYear() - 1)
  else if (range.value === "5y") d.setFullYear(d.getFullYear() - 5)
  return d
}

function formatTickLabel(dateStr, spanDays) {
  if (!dateStr) return ""
  const s = String(dateStr)
  if (spanDays >= 365 * 3) return s.slice(0, 4)
  if (spanDays >= 365) return s.slice(0, 7)
  if (spanDays >= 180) return s.slice(2, 7)
  return s.slice(5)
}

const viewSeries = computed(() => {
  const raw = marketStore.series || []
  if (!raw.length) return []

  const lastDateStr = raw[raw.length - 1]?.date
  const cutoff = subtractRange(lastDateStr)

  let filtered = raw
  if (cutoff) {
    filtered = raw.filter((p) => {
      const dt = parseDate(p.date)
      return dt && dt >= cutoff
    })
  }

  if (interval.value === "week" && filtered.length > 10) {
    const out = []
    for (let i = 0; i < filtered.length; i += 5) out.push(filtered[i])
    const last = filtered[filtered.length - 1]
    if (out[out.length - 1]?.date !== last?.date) out.push(last)
    return out
  }

  return filtered
})

const latestPoint = computed(() => {
  const v = viewSeries.value
  return v.length ? v[v.length - 1] : null
})

function desiredTickCount() {
  if (range.value === "3m") return 6
  if (range.value === "6m") return 6
  if (range.value === "1y") return 7
  if (range.value === "5y") return 8
  return 8
}

function nearestIndexByTime(times, target) {
  let lo = 0, hi = times.length - 1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1
    if (times[mid] < target) lo = mid + 1
    else hi = mid - 1
  }
  if (lo <= 0) return 0
  if (lo >= times.length) return times.length - 1
  const a = times[lo - 1], b = times[lo]
  return Math.abs(a - target) <= Math.abs(b - target) ? lo - 1 : lo
}

function computeTickIndexSet(labels) {
  const n = labels.length
  if (!n) return new Set()

  const k = Math.min(desiredTickCount(), n)
  if (k <= 2) return new Set([0, n - 1])

  const dates = labels.map(parseDate)
  if (dates.some((d) => !d)) {
    const set = new Set([0, n - 1])
    for (let i = 1; i < k - 1; i++) {
      const idx = Math.round((i * (n - 1)) / (k - 1))
      set.add(idx)
    }
    return set
  }

  const times = dates.map((d) => d.getTime())
  const start = times[0]
  const end = times[n - 1]

  const set = new Set([0, n - 1])
  for (let i = 1; i < k - 1; i++) {
    const t = start + ((end - start) * i) / (k - 1)
    set.add(nearestIndexByTime(times, t))
  }
  return set
}

function calcSpanDays(labels) {
  if (!labels?.length) return 0
  const d0 = parseDate(labels[0])
  const d1 = parseDate(labels[labels.length - 1])
  if (!d0 || !d1) return 0
  return Math.round((d1.getTime() - d0.getTime()) / 86400000)
}

// ---------- Chart.js ----------
const LINE_COLOR = "#3b82f6"
const FILL_COLOR = "rgba(59,130,246,0.08)"

function buildOrUpdateChart() {
  if (!canvasEl.value) return

  const labels = viewSeries.value.map((p) => p.date)
  const data = viewSeries.value.map((p) => p.close)

  const tickSet = computeTickIndexSet(labels)
  const spanDays = calcSpanDays(labels)

  const tickCallback = (value, index) => {
    const idx = Number(index)
    if (!Number.isFinite(idx)) return ""
    if (!tickSet.has(idx)) return ""
    return formatTickLabel(labels[idx], spanDays)
  }

  if (!chart) {
    chart = new Chart(canvasEl.value, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: selectedLabel.value,
            data,
            borderColor: LINE_COLOR,
            backgroundColor: FILL_COLOR,
            fill: false,
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.25,
            spanGaps: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: { legend: { display: false } },
        scales: {
          x: {
            ticks: {
              autoSkip: false,
              maxRotation: 0,
              minRotation: 0,
              padding: 6,
              callback: tickCallback,
            },
            grid: { display: false },
          },
          y: {
            ticks: { maxTicksLimit: 6 },
            grid: { display: true },
          },
        },
      },
    })
    return
  }

  chart.data.labels = labels
  chart.data.datasets[0].label = selectedLabel.value
  chart.data.datasets[0].data = data
  chart.data.datasets[0].borderColor = LINE_COLOR
  chart.data.datasets[0].backgroundColor = FILL_COLOR
  chart.options.scales.x.ticks.callback = tickCallback
  chart.options.scales.x.grid.display = false
  chart.update("none")
}

onMounted(async () => {
  try {
    await marketStore.fetchIndexSeries(symbol.value)
    await marketStore.fetchMarketSummary(summaryMarket.value)
    await marketStore.fetchFx()
    buildOrUpdateChart()
  } finally {
    // 모든 데이터 로드 및 차트 렌더링 완료 후 로딩 해제
    initialLoading.value = false
  }
})

watch(symbol, async () => {
  await marketStore.fetchIndexSeries(symbol.value)
  buildOrUpdateChart()
})

watch([range, interval], () => buildOrUpdateChart())

watch(summaryMarket, async () => {
  await marketStore.fetchMarketSummary(summaryMarket.value)
})

watch(viewSeries, () => buildOrUpdateChart())

onBeforeUnmount(() => {
  if (chart) {
    chart.destroy()
    chart = null
  }
})

// ---------- 환율 국기 ----------
const flagMap = { "USD/KRW": usFlag, "JPY/KRW": jpFlag, "EUR/KRW": euFlag, "CNY/KRW": cnFlag }
function flagSrc(pair) { return flagMap[pair] || null }

// ---------- 표시 포맷 ----------
function fmt(n) {
  if (n == null || Number.isNaN(Number(n))) return "-"
  return Number(n).toLocaleString()
}
function fmtSigned(n) {
  if (n == null || Number.isNaN(Number(n))) return "-"
  const x = Number(n)
  return x > 0 ? `+${x.toFixed(2)}` : x.toFixed(2)
}
function signClass(n) {
  const x = Number(n)
  if (Number.isNaN(x)) return ""
  if (x > 0) return "up"
  if (x < 0) return "dn"
  return ""
}

// ✅ 환율: 값/변동폭 표시용(소수 2자리 고정)
function fmtFx(v) {
  const x = Number(v)
  if (!Number.isFinite(x)) return "-"
  return x.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function fmtFxChange(v) {
  const x = Number(v)
  if (!Number.isFinite(x)) return "-"
  // 변동폭은 부호 없이, 화살표가 담당
  return Math.abs(x).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function fmtFxDelta(n) {
  const x = Number(n)
  if (!Number.isFinite(x)) return "-"
  const s = x > 0 ? "+" : ""
  return `${s}${x.toFixed(2)}`
}
function fmtFxPct(v) {
  const x = Number(v)
  if (!Number.isFinite(x)) return "-"
  return (x > 0 ? `+${x.toFixed(2)}` : x.toFixed(2))
}
function arrow(v) {
  const x = Number(v)
  if (!Number.isFinite(x) || x === 0) return "•"
  return x > 0 ? "▲" : "▼"
}

const turnover = computed(() => marketStore.summary?.turnover || {})
const topGainers = computed(() => marketStore.summary?.top?.gainers || [])
const topLosers  = computed(() => marketStore.summary?.top?.losers || [])

function fmtCompact(n, unit = "") {
  const x = Number(n)
  if (!Number.isFinite(x)) return "-"
  if (x >= 1e9) return `${(x / 1e9).toFixed(2)}B ${unit}`.trim()
  if (x >= 1e6) return `${(x / 1e6).toFixed(2)}M ${unit}`.trim()
  return `${x.toLocaleString()} ${unit}`.trim()
}
function fmtWonCompact(n) {
  const x = Number(n)
  if (!Number.isFinite(x)) return "-"
  if (x >= 1e12) return `₩${(x / 1e12).toFixed(2)}조`
  if (x >= 1e8) return `₩${(x / 1e8).toFixed(2)}억`
  if (x >= 1e4) return `₩${(x / 1e4).toFixed(2)}만`
  return `₩${x.toLocaleString()}`
}
</script>

<style scoped>
.krx-wrap {
  max-width: 1120px;
  margin: 0 auto;
  padding: 20px;
  position: relative;
  min-height: 500px;
}

/* 로딩 오버레이 */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 18px;
  z-index: 10;
  gap: 16px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 4px solid rgba(37, 99, 235, 0.15);
  border-top-color: rgba(37, 99, 235, 0.95);
  animation: spin 0.8s linear infinite;
}

.loading-text {
  font-size: 14px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.70);
}

.krx-grid { display: grid; grid-template-columns: 1.35fr 0.65fr; gap: 14px; align-items: start; }
.krx-card { background: rgba(255,255,255,0.9); border-radius: 16px; padding: 16px; border: 1px solid rgba(0,0,0,0.06); overflow: visible; }
.krx-main { min-height: 360px; }
.krx-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.krx-title .t1 { font-size: 18px; font-weight: 900; }
.krx-title .t2 { margin-top: 6px; font-size: 13px; }
.muted { opacity: 0.65; }
.small { font-size: 12px; }
.chg { margin-left: 6px; opacity: 0.75; }

.krx-controls { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
.btn-group { display: flex; gap: 6px; flex-wrap: wrap; }
.btn {
  padding: 8px 10px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.12);
  background: #fff; cursor: pointer; font-weight: 800; font-size: 12px;
  white-space: nowrap;
}
.btn.on { background: rgba(0,0,0,0.06); }

.krx-chart { height: 260px; margin-top: 10px; }
.krx-foot { margin-top: 10px; font-size: 12px; }

/* 환율 */
.krx-side .side-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.refresh {
  padding: 8px 10px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.12);
  background: #fff; cursor: pointer; font-weight: 900; font-size: 12px;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.refresh.loading { opacity: 0.8; }
.refresh.loading .ico { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.err { margin-top: 10px; color: #b00020; font-weight: 800; }

.fx-list { list-style: none; padding: 0; margin: 12px 0 0; display: grid; gap: 10px; }
.fx-item {
  display: flex; justify-content: space-between; gap: 10px; align-items: center;
  padding: 12px; border-radius: 14px; border: 1px solid rgba(0,0,0,0.08);
}
.fx-left { display: flex; gap: 10px; align-items: center; min-width: 0; }
.fx-meta { min-width: 0; }
.flag { width: 28px; height: 20px; border-radius: 6px; object-fit: cover; border: 1px solid rgba(0,0,0,0.08); }
.flag.ph { width: 28px; height: 20px; border-radius: 6px; background: rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.06); }
.pair { font-weight: 900; font-size: 13px; white-space: nowrap; }
.date { font-size: 12px; white-space: nowrap; }

.fx-right { text-align: right; min-width: 120px; }
.fx-row { display: flex; align-items: baseline; justify-content: flex-end; gap: 10px; }
.rate { font-weight: 900; }
.fx-chg { font-size: 12px; font-weight: 900; white-space: nowrap; display: inline-flex; gap: 4px; align-items: center; }
.fx-pct { font-size: 12px; margin-top: 2px; }

.up { color: #d10b2a; }
.dn { color: #1e5eff; }


.dot { opacity: 0.35; margin: 0 6px; }
.mini { font-weight: 900; font-size: 12px; }

/* 시장 요약 */
.krx-summary { margin-top: 14px; }
.sum-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }
.sum-tabs { display: flex; gap: 8px; flex-wrap: wrap; }
.tab {
  padding: 8px 12px; border-radius: 999px; border: 1px solid rgba(0,0,0,0.12);
  background: #fff; cursor: pointer; font-weight: 900; font-size: 12px;
  white-space: nowrap;
}
.tab.on { background: rgba(0,0,0,0.06); }

.sum-grid.sum-grid-3{
  margin-top: 12px;
  display: grid;
  grid-template-columns: 0.8fr 1.1fr 1.1fr;
  gap: 12px;
}
.sum-card {
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 14px;
  padding: 14px;
  min-height: 150px;
  min-width: 0;
}
.sum-title { font-weight: 900; margin-bottom: 10px; }
.sum-row {
  display: grid;
  grid-template-columns: 84px 1fr;
  align-items: center;
  margin: 7px 0;
  column-gap: 10px;
}
.sum-row .k { opacity: 0.7; font-weight: 800; white-space: nowrap; }
.sum-row .v { justify-self: end; font-weight: 900; white-space: nowrap; }
.mt8 { margin-top: 8px; }

/* ✅ 퍼센트 폭 확장(200%+ 안 잘리게) */
.top-row{
  display: grid;
  grid-template-columns: 62px minmax(0, 1fr) 110px;
  gap: 8px;
  align-items: center;
}
.code { font-weight: 900; opacity: 0.85; white-space: nowrap; }
.name{
  font-weight: 800;
  min-width: 0;
  word-break: keep-all;
  overflow-wrap: normal;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pct { font-weight: 900; text-align: right; white-space: nowrap; }

@media (max-width: 960px) {
  .krx-grid { grid-template-columns: 1fr; }
  .sum-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 560px) {
  .sum-grid { grid-template-columns: 1fr; }
}
@media (max-width: 900px){
  .sum-grid.sum-grid-3{ grid-template-columns: 1fr; }
}
</style>
