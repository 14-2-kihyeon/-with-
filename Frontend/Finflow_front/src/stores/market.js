// src/stores/market.js
import { ref } from "vue"
import { defineStore } from "pinia"
import {
  apiGetIndexSeries,
  apiGetMarketSummary,
  apiGetFxSnapshot,
} from "@/api/market"

export const useMarketStore = defineStore("market", () => {
  const loading = ref(false)
  const error = ref(null)

  // ✅ 차트 원본(일봉/주봉 변환은 백엔드 or 프론트에서)
  const series = ref([]) // [{ date:'YYYY-MM-DD', close:number }]

  // ✅ 시장요약 (UI가 쓰기 좋은 형태로 유지)
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

  // ✅ 환율 (UI가 쓰기 좋은 pair/rate로 유지)
  const fx = ref({
    endpoint: "fx_snapshot",
    as_of: null,
    items: [], // [{ pair, rate, change, change_pct, date }]
    detail: null,
    error: null,
  })

  function setError(e) {
    error.value =
      e?.response?.data?.detail ||
      e?.response?.data?.error ||
      e?.message ||
      "요청 중 오류가 발생했습니다."
  }

  // ✅ 1) 지수 시계열
  async function fetchIndexSeries(symbol, { from, to, interval = "day" } = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await apiGetIndexSeries(symbol, { from, to, interval })
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

  // ✅ 2) 시장 요약 (백엔드 top 구조를 UI용 top_gainers/top_losers로 변환)
  async function fetchMarketSummary(market = "ALL", { date, auto = 1 } = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await apiGetMarketSummary(market, { date, auto })
      const data = res.data || {}

      const gainers = data.top?.gainers || data.top_gainers || []
      const losers = data.top?.losers || data.top_losers || []

      const norm = (row) => {
        const r1 = row.r1 ?? row.change_pct
        // ✅ r1이 0.3이면 30%로 보이게
        const pct =
          row.change_pct != null
            ? Number(row.change_pct)
            : (r1 != null ? Number(r1) * 100 : null)

        return {
          code: row.code ?? row.stock__code ?? "-",
          name: row.name ?? row.stock__name ?? "-",
          change_pct: Number.isFinite(pct) ? pct : null,
          close: row.close ?? null,
          volume: row.volume ?? null,
          amount: row.amount ?? null,
        }
      }

      summary.value = {
        ...summary.value,
        ...data,
        market,
        top_gainers: gainers.map(norm),
        top_losers: losers.map(norm),
      }
    } catch (e) {
      setError(e)
      // summary는 이전값 유지
    } finally {
      loading.value = false
    }
  }

  // ✅ 3) 환율 snapshot (symbol/close -> pair/rate 변환)
  async function fetchFx() {
    loading.value = true
    error.value = null
    try {
      const res = await apiGetFxSnapshot()
      const data = res.data || {}

      const items = (data.items || []).map((it) => ({
        pair: it.pair ?? it.symbol ?? it.name, // ✅ symbol -> pair
        date: it.date ?? null,
        rate: Number(it.rate ?? it.value ?? it.close), // ✅ close -> rate
        change: it.change ?? null,
        change_pct: it.change_pct ?? null,
      }))

      fx.value = {
        endpoint: data.endpoint || "fx_snapshot",
        as_of: data.as_of || items.find((x) => x.date)?.date || null,
        items: items.map((x) => ({
          ...x,
          rate: Number.isFinite(x.rate) ? x.rate : null,
        })),
        detail: data.detail ?? null,
        error: data.error ?? null,
      }
    } catch (e) {
      setError(e)
      fx.value = { endpoint: "fx_snapshot", as_of: null, items: [], detail: null, error: error.value }
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
