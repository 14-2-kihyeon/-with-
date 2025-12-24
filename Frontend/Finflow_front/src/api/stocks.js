// src/api/stocks.js
import api from "@/api/axios"

const STOCKS = "/api/stocks"
const MARKET = "/api/stocks/market"

// ----------------------
// Stocks (종목)
// ----------------------
export const apiSearchStocks = (q) => api.get(`${STOCKS}/search/`, { params: { q } })

export const apiGetRecommendations = (params = {}) =>
  api.get(`${STOCKS}/recommendations/`, { params })

export const apiGetStockDetail = (code, params = {}) =>
  api.get(`${STOCKS}/${code}/`, { params })

export const apiGetStockPrices = (code, params = {}) =>
  api.get(`${STOCKS}/${code}/prices/`, { params })

export const apiGetStockNews = (code, params = {}) =>
  api.get(`${STOCKS}/${code}/news/`, { params })

export const apiPostStockExplain = (code, body = {}, params = {}) =>
  api.post(`${STOCKS}/${code}/explain/`, body, { params, timeout: 130000 })

// yfinance 실시간 주가
export const apiGetRealtimePrice = (code) =>
  api.get(`${STOCKS}/${code}/realtime/`)

// yfinance 인트라데이 차트
export const apiGetIntradayPrices = (code, params = {}) =>
  api.get(`${STOCKS}/${code}/intraday/`, { params })

// ----------------------
// Market (지수/시장요약/환율)
// ----------------------

// ✅ (현재 네가 쓰는 방식) 지수 시계열: /api/stocks/market/prices/?symbol=KS11&from=...&to=...
export const apiGetMarketPrices = (symbol, { from, to } = {}) =>
  api.get(`${MARKET}/prices/`, { params: { symbol, from, to } })

// ✅ 시장요약: /api/stocks/market/summary/?market=KOSPI
export const apiGetMarketSummary = (market = "ALL") =>
  api.get(`${MARKET}/summary/`, { params: { market } })

// ✅ 환율: /api/stocks/market/fx/?pairs=USD/KRW,JPY/KRW...
export const apiGetFx = (pairsCsv = "USD/KRW,JPY/KRW,EUR/KRW,CNY/KRW") =>
  api.get(`${MARKET}/fx/`, { params: { pairs: pairsCsv } })

// ----------------------------------------------------
// ✅ 호환용(export 이름 맞춰주기)
// 기존 코드가 apiGetMarketIndexSeries 같은 이름을 import 해도 안 터지게.
// ----------------------------------------------------
export const apiGetMarketIndexSeries = (symbol, params = {}) => {
  // params: { from, to } 형태 기대
  return apiGetMarketPrices(symbol, params)
}

// 만약 너 프로젝트 어딘가에서 스냅샷을 import 하고 있으면 이것도 같이 살려둠.
// (백엔드에 이 URL이 없으면 404는 나지만, 지금처럼 "모듈 로딩 실패"는 안 남)
export const apiGetMarketIndexSnapshot = (params = {}) => {
  return api.get(`${MARKET}/index/snapshot/`, { params })
}
