// src/stores/auth.js
import { ref, computed } from "vue"
import { defineStore } from "pinia"
import axios from "axios"

const API = "http://127.0.0.1:8000"  // django 주소

export const useAuthStore = defineStore("auth", () => {
  const access = ref(localStorage.getItem("access") || "")
  const refresh = ref(localStorage.getItem("refresh") || "")
  const user = ref(null)

  const isLogin = computed(() => !!access.value)

  const setTokens = (a, r) => {
    access.value = a
    refresh.value = r
    localStorage.setItem("access", a)
    localStorage.setItem("refresh", r)
  }

  const clearTokens = () => {
    access.value = ""
    refresh.value = ""
    user.value = null
    localStorage.removeItem("access")
    localStorage.removeItem("refresh")
    // 팝업 "오늘 하루 보지 않기" 설정도 삭제
    localStorage.removeItem("pb_promo_hide_until")
  }

  // ✅ 로그인 (dj-rest-auth)
  const login = async (username, password) => {
    const res = await axios.post(`${API}/accounts/login/`, { username, password })
    // dj-rest-auth + JWT면 보통 access/refresh 줌
    setTokens(res.data.access, res.data.refresh)
    await fetchUser()
  }

  const refreshAccess = async () => {
    const r = await axios.post(`${API}/accounts/token/refresh/`, {
      refresh: refresh.value,
    })
    access.value = r.data.access
    localStorage.setItem("access", r.data.access)
    return r.data.access
  }


  // ✅ 내 정보 가져오기
  const fetchUser = async () => {
    if (!access.value) return

    try {
      const res = await axios.get(`${API}/accounts/user/`, {
        headers: { Authorization: `Bearer ${access.value}` },
      })
      user.value = res.data
    } catch (err) {
      // 네트워크 에러 (서버 꺼짐) - 토큰 제거하고 에러 던지기
      if (!err.response) {
        console.warn("서버 연결 실패, fetchUser 중단")
        clearTokens()
        throw err
      }

      // access 만료되면 refresh로 복구 후 재시도
      if (err.response?.status === 401 && refresh.value) {
        try {
          await refreshAccess()
          const res = await axios.get(`${API}/accounts/user/`, {
            headers: { Authorization: `Bearer ${access.value}` },
          })
          user.value = res.data
          return
        } catch (refreshErr) {
          // refresh 실패 시에도 토큰 제거
          clearTokens()
          throw refreshErr
        }
      }
      throw err
    }
  }

  // ✅ 로그아웃 (refresh 블랙리스트까지 할 거면)
  const logout = async () => {
    try {
      if (refresh.value) {
        await axios.post(
          `${API}/accounts/logout/`,
          { refresh: refresh.value },
          { headers: { Authorization: `Bearer ${access.value}` } }
        )
      }
    } finally {
      clearTokens()
    }
  }

  return { access, refresh, user, isLogin, login, logout, fetchUser, clearTokens }
})
