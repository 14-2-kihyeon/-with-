// src/stores/stocks.js
import { ref } from "vue"
import { defineStore } from "pinia"
import {
  apiSearchStocks,
  apiGetRecommendations,
  apiGetStockDetail,
  apiGetStockPrices,
  apiGetStockNews,
  apiPostStockExplain,
  apiGetMarketSummary,
  apiGetMarketIndexSnapshot,
  apiGetMarketIndexSeries,
} from "@/api/stocks"

export const useStocksStore = defineStore("stocks", () => {
  // 공통 상태
  const loading = ref(false)
  const error = ref(null)

  // 검색
  const searchQuery = ref("")
  const searchResults = ref([])

  // 추천
  const reco = ref({
    endpoint: "recommendations",
    requested_as_of: null,
    as_of_used: null,
    count: 0,
    recommendations: [],
    detail: null,
    error: null,
  })

  // 상세/차트/뉴스/설명
  const detail = ref(null) // stock_detail 응답 그대로
  const prices = ref([])  // prices array
  const news = ref({
    endpoint: "stock_news",
    count: 0,
    items: [],
    news_fetch: null,
  })

  const explain = ref({
    endpoint: "stock_explain",
    question: "",
    answer: "",
    used: { feature_available: false, news_count: 0, news_fetch: null },
    detail: null,
    error: null,
  })


// ✅ 대시보드(시장/지수)
  const dashLoading = ref(false)
  const dashError = ref(null)

  const indexSnapshot = ref({
    endpoint: "market_index_snapshot",
    count: 0,
    items: [],
    detail: null,
    error: null,
  })

  const indexSeries = ref({
    endpoint: "market_index_series",
    symbol: null,
    name: null,
    interval: "day",
    latest: null,
    count: 0,
    series: [],
    detail: null,
    error: null,
  })

  const marketSummary = ref({
    endpoint: "market_summary",
    requested_as_of: null,
    as_of_used: null,
    market: "ALL",
    breadth: { adv: 0, dec: 0, unch: 0, unknown: 0, total: 0 },
    turnover: { volume: null, amount: null },
    top: { gainers: [], losers: [] },
    detail: null,
    error: null,
  })



  function setError(e) {
    const msg =
      e?.response?.data?.detail ||
      e?.response?.data?.error ||
      e?.message ||
      "요청 중 오류가 발생했습니다."
    error.value = msg
  }

  // 1) 검색
  const searchStocks = async () => {
    if (!searchQuery.value.trim()) {
      searchResults.value = []
      return
    }
    loading.value = true
    error.value = null
    try {
      const res = await apiSearchStocks(searchQuery.value.trim())
      searchResults.value = res.data?.results || []
    } catch (e) {
      setError(e)
      searchResults.value = []
    } finally {
      loading.value = false
    }
  }

  // 2) 추천
  const fetchRecommendations = async ({
    date,
    risk = "MID",
    horizon = "MID",
    top = 20,
    auto = 1,
    include_news = 1,
  } = {}) => {
    loading.value = true
    error.value = null
    try {
      const res = await apiGetRecommendations({ date, risk, horizon, top, auto, include_news })
      reco.value = res.data
    } catch (e) {
      setError(e)
      reco.value = {
        endpoint: "recommendations",
        requested_as_of: date || null,
        as_of_used: null,
        count: 0,
        recommendations: [],
        detail: "추천을 불러오지 못했습니다.",
        error: error.value,
      }
    } finally {
      loading.value = false
    }
  }

  // 3) 상세
  const fetchStockDetail = async (code, { date, auto = 1 } = {}) => {
    loading.value = true
    error.value = null
    try {
      const res = await apiGetStockDetail(code, { date, auto })
      detail.value = res.data
    } catch (e) {
      setError(e)
      detail.value = null
    } finally {
      loading.value = false
    }
  }

  // 4) 차트
  const fetchStockPrices = async (code, { from, to } = {}) => {
    loading.value = true
    error.value = null
    try {
      const res = await apiGetStockPrices(code, { from, to })
      prices.value = res.data?.prices || []
    } catch (e) {
      setError(e)
      prices.value = []
    } finally {
      loading.value = false
    }
  }

  // 5) 뉴스(필요시 자동 저장은 백엔드가 처리)
  const fetchStockNews = async (code, { days = 7, limit = 10, refresh = 0 } = {}) => {
    loading.value = true
    error.value = null
    try {
      const res = await apiGetStockNews(code, { days, limit, refresh })
      news.value = res.data
    } catch (e) {
      setError(e)
      news.value = { endpoint: "stock_news", count: 0, items: [], news_fetch: null }
    } finally {
      loading.value = false
    }
  }

  // 6) AI 설명(필요시 refresh_news=1로 뉴스도 같이 당겨오게)
  const askExplain = async (code, { question, date, auto = 1, refresh_news = 1 } = {}) => {
    loading.value = true
    error.value = null
    try {
      const res = await apiPostStockExplain(
        code,
        { question, date },
        { date, auto, refresh_news }
      )
      explain.value = res.data
    } catch (e) {
      setError(e)
      explain.value = {
        endpoint: "stock_explain",
        question: question || "",
        answer: "",
        used: { feature_available: false, news_count: 0, news_fetch: null },
        detail: "AI 설명 요청 실패",
        error: error.value,
      }
    } finally {
      loading.value = false
    }
  }


  // ✅ 7) 지수 스냅샷
  const fetchIndexSnapshot = async ({ symbols } = {}) => {
    dashLoading.value = true
    dashError.value = null
    try {
      const res = await apiGetMarketIndexSnapshot({ symbols })
      indexSnapshot.value = res.data
    } catch (e) {
      const msg =
        e?.response?.data?.detail || e?.response?.data?.error || e?.message || "지수 스냅샷 요청 실패"
      dashError.value = msg
      indexSnapshot.value = { endpoint: "market_index_snapshot", count: 0, items: [], detail: msg, error: msg }
    } finally {
      dashLoading.value = false
    }
  }

  // ✅ 8) 지수 시계열
  const fetchIndexSeries = async (symbol, { from, to, interval = "day" } = {}) => {
    dashLoading.value = true
    dashError.value = null
    try {
      const res = await apiGetMarketIndexSeries(symbol, { from, to, interval })
      indexSeries.value = res.data
    } catch (e) {
      const msg =
        e?.response?.data?.detail || e?.response?.data?.error || e?.message || "지수 시계열 요청 실패"
      dashError.value = msg
      indexSeries.value = {
        endpoint: "market_index_series",
        symbol,
        name: symbol,
        interval,
        latest: null,
        count: 0,
        series: [],
        detail: msg,
        error: msg,
      }
    } finally {
      dashLoading.value = false
    }
  }

  // ✅ 9) 시장 요약(브레드스/거래대금/top movers)
  const fetchMarketSummary = async ({ date, auto = 1, market = "ALL" } = {}) => {
    dashLoading.value = true
    dashError.value = null
    try {
      const res = await apiGetMarketSummary({ date, auto, market })
      marketSummary.value = res.data
    } catch (e) {
      const msg =
        e?.response?.data?.detail || e?.response?.data?.error || e?.message || "시장 요약 요청 실패"
      dashError.value = msg
      marketSummary.value = {
        endpoint: "market_summary",
        requested_as_of: date || null,
        as_of_used: null,
        market,
        breadth: { adv: 0, dec: 0, unch: 0, unknown: 0, total: 0 },
        turnover: { volume: null, amount: null },
        top: { gainers: [], losers: [] },
        detail: msg,
        error: msg,
      }
    } finally {
      dashLoading.value = false
    }
  }



  return {
    loading,
    error,

    searchQuery,
    searchResults,
    reco,

    detail,
    prices,
    news,
    explain,

    searchStocks,
    fetchRecommendations,
    fetchStockDetail,
    fetchStockPrices,
    fetchStockNews,
    askExplain,

    dashLoading,
    dashError,
    indexSnapshot,
    indexSeries,
    marketSummary,
    fetchIndexSnapshot,
    fetchIndexSeries,
    fetchMarketSummary,
  }
})
