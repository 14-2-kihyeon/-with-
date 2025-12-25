
// 프론트에서 백에 api를 통해 요청할 때 필요한 header, Bearer를 매번 붙이기 
// 귀찮을 경우. 따로 axios.js를 만들어서 관리
// axios “자동으로 토큰 붙이기”

// src/api/axios.js
import axios from "axios"
import { useAuthStore } from "@/stores/auth"

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
})

api.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.access) config.headers.Authorization = `Bearer ${auth.access}`
  return config
})

// 401이면 refresh로 access 재발급 → 원요청 재시도
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const auth = useAuthStore()
    const original = err.config

    // 네트워크 에러 (서버 꺼짐) 시 토큰 제거
    if (!err.response) {
      console.warn("서버 연결 실패, 토큰 제거:", err.message || "NETWORK_ERROR")
      auth.clearTokens()
      return Promise.reject(err)
    }

    if (err.response?.status === 401 && !original._retry && auth.refresh) {
      original._retry = true
      try {
        const r = await axios.post("http://127.0.0.1:8000/accounts/token/refresh/", {
          refresh: auth.refresh,
        })
        auth.access = r.data.access
        localStorage.setItem("access", r.data.access)
        original.headers.Authorization = `Bearer ${r.data.access}`
        if (r.data.refresh) {                 // ✅ rotate 켜져 있으면 refresh도 같이 옴
          auth.refresh = r.data.refresh
          localStorage.setItem("refresh", r.data.refresh)
        }
        return api(original)
      } catch (refreshErr) {
        // refresh 실패 시에도 네트워크 에러인지 확인
        console.warn("토큰 갱신 실패:", refreshErr.message || "REFRESH_FAILED")
        auth.clearTokens()
      }
    }
    return Promise.reject(err)
  }
)

export default api
