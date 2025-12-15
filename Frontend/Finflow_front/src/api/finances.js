import api from "@/api/axios"

// ✅ 은행(금융회사) 목록
export const getBanks = async () => {
  const res = await api.get("/finances/banks/")
  return res.data // ["국민은행", "신한은행", ...]
}

// ✅ 예금 상품 목록 (bank 없으면 전체)
export const getDeposits = async (bank = "") => {
  const res = await api.get("/finances/deposits/", {
    params: bank ? { bank } : {},
  })
  return res.data // [{ fin_prdt_cd, kor_co_nm, fin_prdt_nm }, ...]
}

// ✅ 예금 상품 디테일 (옵션 포함)
export const getDepositDetail = async (fin_prdt_cd) => {
  const res = await api.get(`/finances/deposits/${fin_prdt_cd}/`)
  return res.data
}


// (선택) 적금 동기화 - 화면에서 자주 안 쓰면 버튼으로만
// export const syncSavings = () => api.get("/finances/savings/sync/")

// ✅ 적금 은행 목록
export const getSavingBanks = async () => {
  // 너의 백엔드가 /finances/savings/banks/ 를 안 만들고
  // /finances/banks/ 만 재사용 중일 수도 있어서 fallback 처리
  try {
    const res = await api.get("/finances/savings/banks/")
    return res.data
  } catch (e) {
    const res = await api.get("/finances/banks/")
    return res.data
  }
}

// ✅ 적금 상품 리스트 (bank 쿼리 지원: ?bank=국민은행)
export const getSavings = (bank = "") => {
  return api.get("/finances/savings/", {
    params: bank ? { bank } : {},
  })
}

// ✅ 적금 상품 상세
export const getSavingDetail = (fin_prdt_cd) => {
  return api.get(`/finances/savings/${fin_prdt_cd}/`)
}