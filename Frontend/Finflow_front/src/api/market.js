// src/api/market.js
import api from "@/api/axios"

const BASE = "/api/stocks/market"

// ✅ 지수 시계열 (urls.py: market/index/<symbol>/series/)
export const apiGetIndexSeries = (symbol, params = {}) => {
  return api.get(`${BASE}/index/${symbol}/series/`, { params })
}

// ✅ 지수 스냅샷 (urls.py: market/index/snapshot/)
export const apiGetIndexSnapshot = (params = {}) => {
  return api.get(`${BASE}/index/snapshot/`, { params })
}

// ✅ 시장 요약 (urls.py: market/summary/)
export const apiGetMarketSummary = (market = "ALL", params = {}) => {
  return api.get(`${BASE}/summary/`, { params: { market, ...params } })
}

// ✅ 지수 prices (urls.py: market/prices/) - 필요하면 사용
export const apiGetMarketPrices = (symbol, params = {}) => {
  return api.get(`${BASE}/prices/`, { params: { symbol, ...params } })
}

// ✅ 환율 snapshot (urls.py: market/fx/snapshot/)
export const apiGetFxSnapshot = () => {
  return api.get(`${BASE}/fx/snapshot/`)
}

// ✅ 환율 latest (urls.py: market/fx/)
export const apiGetFxLatest = (pairsCsv = "USD/KRW,JPY/KRW,EUR/KRW,CNY/KRW") => {
  return api.get(`${BASE}/fx/`, { params: { pairs: pairsCsv } })
}
