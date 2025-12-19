// src/api/finances.js

import api from "./axios"

// ============================================
// 예금
// ============================================

/**
 * 금융감독원 API에서 예금 데이터 가져와 DB 저장
 */
export const syncDeposits = async () => {
  const res = await api.get("/finances/deposits/sync/")
  return res.data
}

/**
 * 은행 목록 조회
 */
export const getBanks = async () => {
  const res = await api.get("/finances/banks/")
  return res.data
}

/**
 * 예금 상품 목록 조회
 * @param {string} bank - 은행명 (선택)
 */
export const getDeposits = async (bank = "") => {
  const params = bank ? { bank } : {}
  const res = await api.get("/finances/deposits/", { params })
  return res.data
}

/**
 * 예금 상품 상세 조회
 * @param {string} fin_prdt_cd - 상품코드
 */
export const getDepositDetail = async (fin_prdt_cd) => {
  const res = await api.get(`/finances/deposits/${fin_prdt_cd}/`)
  return res.data
}


// ============================================
// 적금
// ============================================

/**
 * 금융감독원 API에서 적금 데이터 가져와 DB 저장
 */
export const syncSavings = async () => {
  const res = await api.get("/finances/savings/sync/")
  return res.data
}

/**
 * 적금 은행 목록
 */
export const getSavingBanks = async () => {
  const res = await api.get("/finances/savings/banks/")
  return res.data
}

/**
 * 적금 상품 목록
 * @param {string} bank - 은행명 (선택)
 */
export const getSavings = async (bank = "") => {
  const params = bank ? { bank } : {}
  const res = await api.get("/finances/savings/", { params })
  return res
}

/**
 * 적금 상품 상세
 * @param {string} fin_prdt_cd - 상품코드
 */
export const getSavingDetail = async (fin_prdt_cd) => {
  const res = await api.get(`/finances/savings/${fin_prdt_cd}/`)
  return res
}