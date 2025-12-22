// src/api/market.js
import axios from "axios"

const BASE = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000"

const marketClient = axios.create({
  baseURL: `${BASE}/api/stocks/market/`,
  timeout: 20000,
})

// 1) 지수 시계열: /market/index/<symbol>/series/
export const apiGetIndexSeries = (symbol, { from, to, interval = "day" } = {}) => {
  return marketClient.get(`index/${symbol}/series/`, {
    params: { from, to, interval },
  })
}

// 2) 시장 요약: /market/summary/
export const apiGetMarketSummary = (market = "ALL", { date, auto = 1 } = {}) => {
  return marketClient.get("summary/", {
    params: { market, date, auto },
  })
}

// 3) 환율 스냅샷: /market/fx/snapshot/
export const apiGetFxSnapshot = () => {
  return marketClient.get("fx/snapshot/")
}

// (선택) 지수 스냅샷 리스트: /market/index/snapshot/
export const apiGetIndexSnapshot = (symbolsCsv) => {
  return marketClient.get("index/snapshot/", {
    params: symbolsCsv ? { symbols: symbolsCsv } : {},
  })
}
