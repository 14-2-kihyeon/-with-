// src/api/stocks.js
import axios from "axios"

// 백엔드 주소 (Vite 환경변수 있으면 그거 사용)
const BASE = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000"

const stocksClient = axios.create({
  baseURL: `${BASE}/api/stocks/`,
  timeout: 20000,
})

export function apiSearchStocks(q) {
  return stocksClient.get("search/", { params: { q } })
}

export function apiGetRecommendations(params = {}) {
  // params: { date, risk, horizon, top, auto, include_news }
  return stocksClient.get("recommendations/", { params })
}

export function apiGetStockDetail(code, params = {}) {
  // params: { date, auto }
  return stocksClient.get(`${code}/`, { params })
}

export function apiGetStockPrices(code, params = {}) {
  // params: { from, to }
  return stocksClient.get(`${code}/prices/`, { params })
}

export function apiGetStockNews(code, params = {}) {
  // params: { days, limit, refresh }
  return stocksClient.get(`${code}/news/`, { params })
}

export function apiPostStockExplain(code, body = {}, params = {}) {
  // params: { date, auto, refresh_news }
  // body: { question, date(optional) }
  return stocksClient.post(`${code}/explain/`, body, {
    params,
    // AI 응답이 길어질 수 있으니 timeout 길게
    timeout: 130000,
  })
}
