<template>
  <section class="np-card">
    <!-- 로딩 오버레이 -->
    <div v-if="initialLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">차트 데이터를 불러오는 중...</div>
    </div>

    <!-- 메인 컨텐츠 -->
    <div v-show="!initialLoading">
      <!-- 헤더 -->
      <div class="np-head">
        <div class="np-title">
          <div class="kicker">현물</div>
          <div class="title">금/은 가격 비교</div>
        </div>

        <div class="np-actions">
          <button
            class="seg"
            :class="{ active: assetType === 'gold' }"
            type="button"
            @click="setAsset('gold')"
          >
            금
          </button>
          <button
            class="seg"
            :class="{ active: assetType === 'silver' }"
            type="button"
            @click="setAsset('silver')"
          >
            은
          </button>
        </div>
      </div>

      <!-- 컨트롤 -->
      <div class="np-controls">
        <div class="field">
          <div class="label">시작</div>
          <input class="input" type="date" v-model="startDate" />
        </div>

        <div class="field">
          <div class="label">종료</div>
          <input class="input" type="date" v-model="endDate" />
        </div>

        <button class="btn" type="button" :disabled="loading" @click="fetchPriceData">
          <span v-if="loading" class="spinner" />
          조회
        </button>
      </div>

      <p v-if="errorMessage" class="np-error">{{ errorMessage }}</p>

      <!-- 차트 -->
      <div class="np-chart">
        <canvas ref="chartEl" />
      </div>

      <div class="np-foot">
        <div class="foot-left">최신 조회 기준 표시</div>
        <div class="foot-right">© 2025 Bankbook</div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from "vue"
import Chart from "chart.js/auto"
import "chartjs-adapter-date-fns"

const assetType = ref("gold")
const startDate = ref("2023-01-01")
const endDate = ref("2024-12-31")

const loading = ref(false)
const initialLoading = ref(true) // 최초 로딩 상태
const errorMessage = ref("")

const priceData = ref([])

const chartEl = ref(null)
let chartInstance = null

const setAsset = async (type) => {
  assetType.value = type
  await fetchPriceData()
}

const normalize = (data) => {
  // 백엔드 응답이 {Date, Close/Last} 형태라고 가정 (기존 코드 유지)
  // gold는 문자열 콤마 제거 처리
  if (assetType.value === "gold") {
    return data.map((item) => ({
      Date: item.Date,
      "Close/Last": typeof item["Close/Last"] === "string"
        ? parseFloat(item["Close/Last"].replace(/,/g, ""))
        : Number(item["Close/Last"]),
    }))
  }
  return data.map((item) => ({
    Date: item.Date,
    "Close/Last": typeof item["Close/Last"] === "string"
      ? Number(item["Close/Last"])
      : Number(item["Close/Last"]),
  }))
}

const fetchPriceData = async () => {
  errorMessage.value = ""
  loading.value = true

  try {
    // 기본값 보정
    if (!startDate.value) startDate.value = "2023-01-01"
    if (!endDate.value) endDate.value = "2024-12-31"

    if (new Date(startDate.value) > new Date(endDate.value)) {
      errorMessage.value = "시작일이 종료일보다 클 수 없습니다."
      return
    }

    const url = `http://127.0.0.1:8000/gold_silver/get_price_data/?asset_type=${assetType.value}&start_date=${startDate.value}&end_date=${endDate.value}`
    const response = await fetch(url)
    const data = await response.json()

    if (data.status !== "success") {
      errorMessage.value = "데이터 조회에 실패했습니다."
      return
    }

    priceData.value = normalize(data.data || [])
    await nextTick()
    renderChart()

    // 차트 렌더링 완료 후 최초 로딩 상태 해제
    if (initialLoading.value) {
      await nextTick()
      initialLoading.value = false
    }
  } catch (e) {
    console.error(e)
    errorMessage.value = "서버와의 연결에 실패했습니다."
    // 에러 발생해도 최초 로딩은 해제
    if (initialLoading.value) {
      initialLoading.value = false
    }
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartEl.value) return
  const ctx = chartEl.value.getContext("2d")

  // 기존 차트 제거
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  const dates = priceData.value.map((item) => new Date(item.Date))
  const prices = priceData.value.map((item) => Number(item["Close/Last"]))

  // 데이터 없으면 안내만
  if (!dates.length || !prices.length) {
    return
  }

  const minY = Math.min(...prices)
  const maxY = Math.max(...prices)
  const pad = (maxY - minY) * 0.08 || 1

  chartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: dates,
      datasets: [
        {
          label: assetType.value === "gold" ? "금 가격" : "은 가격",
          data: prices,
          fill: false,
          tension: 0, // 곡선 제거: 0으로 설정하여 직선으로 표시
          pointRadius: 3, // 점 표시
          pointBackgroundColor: assetType.value === "gold" ? "rgba(255, 193, 7, 0.9)" : "rgba(156, 163, 175, 0.9)",
          pointBorderColor: "#fff",
          pointBorderWidth: 1,
          pointHoverRadius: 5,
          borderWidth: 2,
          borderColor: assetType.value === "gold" ? "rgba(255, 193, 7, 0.8)" : "rgba(156, 163, 175, 0.8)",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true },
        tooltip: { mode: "index", intersect: false },
      },
      interaction: { mode: "index", intersect: false },
      scales: {
        x: {
          type: "time",
          time: { unit: "month" },
          grid: { display: false },
          ticks: { maxRotation: 0 },
        },
        y: {
          grid: { color: "rgba(15,23,42,0.06)" },
          ticks: { callback: (v) => `${v}` },
          suggestedMin: minY - pad,
          suggestedMax: maxY + pad,
        },
      },
    },
  })
}

onMounted(async () => {
  await fetchPriceData()
})

onBeforeUnmount(() => {
  if (chartInstance) chartInstance.destroy()
})

// 날짜 변경 후 자동 조회를 원하면 주석 해제
watch([startDate, endDate], () => {
  // 너무 잦은 호출이 싫으면 버튼 조회만 유지하고 이 watch는 제거
})
</script>

<style scoped>
/* 빨간 영역에 들어가는 Npay 카드 */
.np-card {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  padding: 18px;
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

/* Header */
.np-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.kicker {
  font-size: 12px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.55);
}

.title {
  font-size: 16px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.95);
  margin-top: 2px;
}

.np-actions {
  display: inline-flex;
  padding: 6px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.04);
  border: 1px solid rgba(15, 23, 42, 0.08);
  gap: 6px;
}

.seg {
  height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  border: 0;
  background: transparent;
  font-weight: 900;
  cursor: pointer;
  color: rgba(15, 23, 42, 0.65);
}

.seg.active {
  background: rgba(37, 99, 235, 0.12);
  color: rgba(37, 99, 235, 0.95);
}

/* Controls */
.np-controls {
  display: grid;
  grid-template-columns: 1fr 1fr 120px;
  gap: 10px;
  align-items: end;
  margin-top: 6px;
}

.field .label {
  font-size: 12px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.55);
  margin-bottom: 6px;
}

.input {
  width: 100%;
  height: 42px;
  border-radius: 14px;
  border: 1px solid rgba(15, 23, 42, 0.10);
  background: rgba(255, 255, 255, 0.75);
  padding: 0 12px;
  outline: none;
}

.input:focus {
  border-color: rgba(37, 99, 235, 0.35);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.10);
}

.btn {
  height: 42px;
  border: 0;
  border-radius: 14px;
  background: rgba(37, 99, 235, 0.95);
  color: #fff;
  font-weight: 900;
  cursor: pointer;
  box-shadow: 0 18px 36px rgba(37, 99, 235, 0.18);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  margin-right: 8px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.55);
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
  vertical-align: -2px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.np-error {
  margin-top: 10px;
  color: #c00;
  font-weight: 800;
}

/* Chart */
.np-chart {
  margin-top: 14px;
  border-radius: 16px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.75);
  padding: 12px;
  height: 360px; /* 빨간 영역에 자연스럽게 */
}

/* Footer */
.np-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.55);
  font-weight: 700;
}

@media (max-width: 860px) {
  .np-controls {
    grid-template-columns: 1fr 1fr;
  }
  .btn {
    grid-column: 1 / -1;
  }
  .np-chart {
    height: 320px;
  }
}
</style>
