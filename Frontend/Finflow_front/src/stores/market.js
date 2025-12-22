// src/stores/market.js
import { ref } from "vue"
import { defineStore } from "pinia"
import { apiGetIndexSeries, apiGetMarketSummary, apiGetFxSnapshot } from "@/api/market"

export const useMarketStore = defineStore("market", () => {
  const loading = ref(false)
  const error = ref(null)

  // 차트 시계열(표준 형태): [{date, close}]
  const series = ref([])

  // 시장요약(표준 형태)
  const summary = ref({
    endpoint: "market_summary",
    requested_as_of: null,
    as_of_used: null,
    market: "ALL",
    breadth: { adv: 0, dec: 0, unch: 0, unknown: 0, total: 0 },
    turnover: { volume: null, amount: null },
    top_gainers: [],
    top_losers: [],
    detail: null,
    error: null,
  })

  // 환율(표준 형태)
  const fx = ref({
    endpoint: "fx_snapshot",
    as_of: null,
    items: [], // [{ pair, date, rate, change, change_pct }]
  })

  function setError(e) {
    error.value =
      e?.response?.data?.detail ||
      e?.response?.data?.error ||
      e?.message ||
      "요청 중 오류가 발생했습니다."
  }

  // 1) 지수 시계열
  async function fetchIndexSeries(symbol, { from, to, interval = "day" } = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await apiGetIndexSeries(symbol, { from, to, interval })

      // 백엔드: { series: [{date, close, ...}] }
      const arr = res.data?.series || []
      series.value = arr
        .map((x) => ({
          date: x.date,
          close: Number(x.close),
        }))
        .filter((x) => x.date && Number.isFinite(x.close))
    } catch (e) {
      setError(e)
      series.value = []
    } finally {
      loading.value = false
    }
  }

  // 2) 시장 요약
  async function fetchMarketSummary(market = "ALL", { date, auto = 1 } = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await apiGetMarketSummary(market, { date, auto })
      const d = res.data || {}

      // 백엔드: top: {gainers, losers}
      summary.value = {
        ...d,
        top_gainers: d.top_gainers || d.top?.gainers || [],
        top_losers: d.top_losers || d.top?.losers || [],
      }
    } catch (e) {
      setError(e)
      // 기존 summary 유지
    } finally {
      loading.value = false
    }
  }

  // 3) 환율 스냅샷
  async function fetchFx() {
    loading.value = true
    error.value = null
    try {
      const res = await apiGetFxSnapshot()
      const d = res.data || {}
      const rawItems = d.items || []

      // 백엔드: {symbol, close, date, change, change_pct}
      const items = rawItems.map((it) => ({
        pair: it.pair || it.symbol,          // 표준화
        date: it.date || null,
        rate: it.rate ?? it.value ?? it.close ?? null, // 표준화
        change: it.change ?? null,
        change_pct: it.change_pct ?? null,
      }))

      const as_of = items.find((x) => x.date)?.date || null
      fx.value = { endpoint: d.endpoint || "fx_snapshot", as_of, items }
    } catch (e) {
      setError(e)
      fx.value = { endpoint: "fx_snapshot", as_of: null, items: [] }
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    series,
    summary,
    fx,
    fetchIndexSeries,
    fetchMarketSummary,
    fetchFx,
  }
})
