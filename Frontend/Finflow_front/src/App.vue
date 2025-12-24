<template>
  <div class="fontfont">
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
      console.warn("토큰 검증 실패, 자동 로그아웃:", err.message)
      auth.clearTokens()
    }
  }
})
</script>

<style scoped>
  /* font-weight : 100 ~ 900 각 뷰에서 설정 */
.fontfont {
  font-family: 'Pretendard';
}
</style>