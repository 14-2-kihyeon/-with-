<template>
  <RouterView />
  <!-- 모든 페이지에서 챗봇 위젯 표시 -->
  <ChatbotWidget />
</template>

<script setup>
import NavBar from "@/components/common/NavBar.vue"
import ChatbotWidget from "@/components/common/ChatbotWidget.vue"
import { onMounted } from "vue"
import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()

onMounted(() => {
  // access가 있으면 user 복구
  if (auth.isLogin && !auth.user) auth.fetchUser()
})
</script>

<style scoped>

</style>