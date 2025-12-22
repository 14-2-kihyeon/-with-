<template>
  <div class="chart-wrap">
    <canvas ref="canvasEl"></canvas>
    <p v-if="!prices?.length" class="empty">가격 데이터가 없습니다.</p>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue"
import Chart from "chart.js/auto"

const props = defineProps({
  prices: { type: Array, default: () => [] },
})

const canvasEl = ref(null)
let chart = null

const render = () => {
  if (!canvasEl.value) return
  const labels = (props.prices || []).map(p => p.date)
  const data = (props.prices || []).map(p => p.close)

  if (chart) {
    chart.destroy()
    chart = null
  }

  if (!labels.length) return

  chart = new Chart(canvasEl.value.getContext("2d"), {
    type: "line",
    data: {
      labels,
      datasets: [{ label: "Close", data }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: { ticks: { maxTicksLimit: 8 } },
      },
    },
  })
}

onMounted(render)

watch(
  () => props.prices,
  () => render(),
  { deep: true }
)

onBeforeUnmount(() => {
  if (chart) chart.destroy()
})
</script>

<style scoped>
.chart-wrap { position: relative; height: 320px; }
.empty { margin-top: 10px; opacity: 0.7; }
</style>
