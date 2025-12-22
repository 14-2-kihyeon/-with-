<template>
  <section class="krx-wrap">
    <div class="krx-grid">
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
              <div class="rate">
                {{ it.rate ?? it.value ?? it.close }}
              </div>
              <div class="delta" :class="signClass(it.change)">
                {{ it.change == null ? "-" : `${fmtSigned(it.change)} (${fmtSigned(it.change_pct)}%)` }}
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <!-- 시장 요약 -->
    <div class="krx-card krx-summary">
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
            <span class="pct up">{{ fmtSigned((it.r1 ?? 0) * 100) }}%</span>
          </div>
        </div>

        <div class="sum-card">
          <div class="sum-title">하락 Top 5</div>
          <div v-if="!topLosers.length" class="muted small">데이터 없음</div>
          <div v-for="it in topLosers" :key="it.code" class="top-row">
            <span class="code">{{ it.code }}</span>
            <span class="name" :title="it.name">{{ it.name }}</span>
            <span class="pct dn">{{ fmtSigned((it.r1 ?? 0) * 100) }}%</span>
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

// ✅ assets 국기
import usFlag from "@/assets/flag/us.png"
import jpFlag from "@/assets/flag/jp.png"
import euFlag from "@/assets/flag/eu.png"
import cnFlag from "@/assets/flag/cn.png"

const marketStore = useMarketStore()

const canvasEl = ref(null)
let chart = null

// 차트 선택 상태
const symbol = ref("KS11")
const selectedLabel = ref("KOSPI")

// interval/range
const interval = ref("day") // day | week
const range = ref("all")    // 3m | 6m | 1y | 5y | all

// 시장요약 탭
const summaryMarket = ref("ALL")

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
    // ✅ 데이터가 같아도 "모션"이 보이도록 최소 시간 보장
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



// ---------- 날짜 유틸 ----------
function parseDate(s) {
  if (!s) return null
  // 이미 Date로 들어오는 경우도 방어
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

// 기간(span)에 따라 라벨을 자동 축약 (ALL일 때 특히 중요)
function formatTickLabel(dateStr, spanDays) {
  if (!dateStr) return ""

  // spanDays가 계산 안되면 fallback
  const s = String(dateStr)

  // 3년 이상: YYYY
  if (spanDays >= 365 * 3) return s.slice(0, 4)
  // 1년 이상: YYYY-MM
  if (spanDays >= 365) return s.slice(0, 7)
  // 6개월 이상: YY-MM
  if (spanDays >= 180) return s.slice(2, 7)
  // 그 외: MM-DD
  return s.slice(5)
}

// ---------- 데이터 뷰 (range/interval 반영) ----------
const viewSeries = computed(() => {
  const raw = marketStore.series || []
  if (!raw.length) return []

  // 1) range 필터
  const lastDateStr = raw[raw.length - 1]?.date
  const cutoff = subtractRange(lastDateStr)

  let filtered = raw
  if (cutoff) {
    filtered = raw.filter((p) => {
      const dt = parseDate(p.date)
      return dt && dt >= cutoff
    })
  }

  // 2) week 다운샘플: “대충 5거래일마다”
  if (interval.value === "week" && filtered.length > 10) {
    const out = []
    for (let i = 0; i < filtered.length; i += 5) out.push(filtered[i])
    // 마지막 값 보장
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

// ---------- ✅ “시작~끝을 N등분해서” 라벨 인덱스 선택 ----------
function desiredTickCount() {
  // ALL이 제일 길어서 라벨이 길게 겹침 → 개수 줄임
  if (range.value === "3m") return 6
  if (range.value === "6m") return 6
  if (range.value === "1y") return 7
  if (range.value === "5y") return 8
  return 8 // all
}

function nearestIndexByTime(times, target) {
  let lo = 0,
    hi = times.length - 1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1
    if (times[mid] < target) lo = mid + 1
    else hi = mid - 1
  }
  if (lo <= 0) return 0
  if (lo >= times.length) return times.length - 1
  const a = times[lo - 1],
    b = times[lo]
  return Math.abs(a - target) <= Math.abs(b - target) ? lo - 1 : lo
}

function computeTickIndexSet(labels) {
  const n = labels.length
  if (!n) return new Set()

  const k = Math.min(desiredTickCount(), n)
  if (k <= 2) return new Set([0, n - 1])

  // 날짜 파싱
  const dates = labels.map(parseDate)
  // 파싱 실패가 하나라도 있으면 균등 인덱스로 fallback
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
    const idx = nearestIndexByTime(times, t)
    set.add(idx)
  }
  return set
}

// spanDays 계산(라벨 축약용)
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
              autoSkip: false,     // ✅ autoSkip 끄고, 우리가 고른 것만 보이게
              maxRotation: 0,
              minRotation: 0,
              padding: 6,
              callback: tickCallback,
            },
            grid: {
              display: false,      // ✅ 세로줄 제거(회색 배경 방지)
            },
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

  chart.options.scales.x.ticks.autoSkip = false
  chart.options.scales.x.ticks.callback = tickCallback
  chart.options.scales.x.grid.display = false

  chart.update("none")
}

onMounted(async () => {
  await marketStore.fetchIndexSeries(symbol.value)
  await marketStore.fetchMarketSummary(summaryMarket.value)
  await marketStore.fetchFx()
  buildOrUpdateChart()
})

watch(symbol, async () => {
  await marketStore.fetchIndexSeries(symbol.value)
  buildOrUpdateChart()
})

watch([range, interval], () => {
  // viewSeries가 바뀌니 차트 갱신
  buildOrUpdateChart()
})

watch(summaryMarket, async () => {
  await marketStore.fetchMarketSummary(summaryMarket.value)
})

watch(viewSeries, () => {
  buildOrUpdateChart()
})

onBeforeUnmount(() => {
  if (chart) {
    chart.destroy()
    chart = null
  }
})

// ---------- 환율 국기 ----------
const flagMap = {
  "USD/KRW": usFlag,
  "JPY/KRW": jpFlag,
  "EUR/KRW": euFlag,
  "CNY/KRW": cnFlag,
}
function flagSrc(pair) {
  return flagMap[pair] || null
}

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

const breadth = computed(() => marketStore.summary?.breadth || {})
const turnover = computed(() => marketStore.summary?.turnover || {})
const topGainers = computed(() => marketStore.summary?.top_gainers || marketStore.summary?.top?.gainers || [])
const topLosers = computed(() => marketStore.summary?.top_losers || marketStore.summary?.top?.losers || [])

function safeNum(n) {
  if (n == null) return "-"
  return Number(n).toLocaleString()
}

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

// Top5 퍼센트 표시(네 백엔드가 r1을 주면 r1%로 표시)
function pctFrom(it) {
  const v = it?.change_pct ?? it?.r1
  if (v == null || Number.isNaN(Number(v))) return "-"
  const x = Number(v)
  return `${x > 0 ? "+" : ""}${x.toFixed(2)}%`
}
</script>

<style scoped>
/* 전체 */
.krx-wrap { max-width: 1120px; margin: 0 auto; padding: 20px; }
.krx-grid { display: grid; grid-template-columns: 1.35fr 0.65fr; gap: 14px; align-items: start; }
.krx-card { background: rgba(255,255,255,0.9); border-radius: 16px; padding: 16px; border: 1px solid rgba(0,0,0,0.06); overflow: visible; }
.krx-main { min-height: 360px; }
.krx-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.krx-title .t1 { font-size: 18px; font-weight: 900; }
.krx-title .t2 { margin-top: 6px; font-size: 13px; }
.muted { opacity: 0.65; }
.small { font-size: 12px; }
.chg { margin-left: 6px; opacity: 0.75; }

/* 버튼 */
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
}
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
.fx-right { text-align: right; }
.rate { font-weight: 900; }
.delta { font-size: 12px; font-weight: 900; }
.up { color: #d10b2a; }
.dn { color: #1e5eff; }

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

/* ✅ 3+1 방지: 데스크탑은 무조건 4열, 줄어들면 2열/1열 */
.sum-grid.sum-grid-3{
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
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

/* ✅ 상승/하락 잘림 방지(라벨 폭 확보 + nowrap) */
.sum-row {
  display: grid;
  grid-template-columns: 84px 1fr;
  align-items: center;
  margin: 7px 0;
  column-gap: 10px;
}
.sum-row .k {
  opacity: 0.7;
  font-weight: 800;
  white-space: nowrap;
}
.sum-row .v {
  justify-self: end;
  font-weight: 900;
  white-space: nowrap;
}

.mt8 { margin-top: 8px; }

.top-row{
  display: grid;
  grid-template-columns: 62px minmax(0, 1fr) 74px; /* ✅ 이름 칸 넓히기 */
  gap: 8px;
  align-items: center;
}
.code { font-weight: 900; opacity: 0.85; white-space: nowrap; }
/* 기존 .name 교체 */
.name{
  font-weight: 800;
  min-width: 0;

  /* ✅ 글자단위로 세로 내려가는 현상 방지 */
  word-break: keep-all;
  overflow-wrap: normal;

  /* ✅ 한 줄만 보여주고 ... */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pct { font-weight: 900; text-align: right; white-space: nowrap; }


.refresh {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.refresh .ico {
  display: inline-block;
}

.refresh.loading {
  opacity: 0.8;
}

.refresh.loading .ico {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}



/* 반응형 */
@media (max-width: 960px) {
  .krx-grid { grid-template-columns: 1fr; }
  .sum-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } /* ✅ 2열 고정 */
}
@media (max-width: 560px) {
  .sum-grid { grid-template-columns: 1fr; } /* ✅ 1열 고정 */
}

@media (max-width: 900px){
  .sum-grid.sum-grid-3{
    grid-template-columns: 1fr;
  }
}

</style>
