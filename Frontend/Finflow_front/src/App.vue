<template>
  <div id="app">
    <RouterView />
    <!-- 모든 페이지에서 챗봇 위젯 표시 -->
    <ChatbotWidget />
    <!-- 맨 위로 가기 버튼 -->
    <ScrollToTop />
  </div>
</template>

<script setup>
import ChatbotWidget from "@/components/common/ChatbotWidget.vue"
import ScrollToTop from "@/components/common/ScrollToTop.vue"
import { onMounted } from "vue"
import { useAuthStore } from "@/stores/auth"
const auth = useAuthStore()

onMounted(async () => {
  // access가 있으면 user 복구 시도, 실패하면 로그아웃
  if (auth.isLogin && !auth.user) {
    try {
      await auth.fetchUser()
    } catch (err) {
      // 서버가 응답하지 않거나 토큰이 무효하면 자동 로그아웃
      // 네트워크 에러(ERR_CONNECTION_REFUSED 등), 401, 403 등 모든 에러 처리
      console.warn("토큰 검증 실패, 자동 로그아웃:", err.message || err.code || "NETWORK_ERROR")
      auth.clearTokens()
    }
  }
})
</script>

<style>
/* 전역 스타일 - font.css에서 폰트 설정을 상속받음 */
/* font-weight는 각 컴포넌트에서 100~900 사이의 값으로 자유롭게 설정 가능 */
#app {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>