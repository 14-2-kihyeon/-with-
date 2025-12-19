<template>
  <nav class="nav">
    <RouterLink :to="{ name: 'main' }">Main</RouterLink>
    <RouterLink :to="{ name: 'post_list' }">Posts</RouterLink>
    <RouterLink :to="{ name: 'deposit_list' }">Deposits</RouterLink>
    <RouterLink :to="{ name: 'saving_list' }">Savings</RouterLink>
    <RouterLink :to="{ name: 'naver_news' }">Naver News</RouterLink>
    <RouterLink :to="{ name: 'bank_map' }">KaKao Map</RouterLink>
    <RouterLink :to="{ name: 'youtube_search' }">YouTube</RouterLink>

    <RouterLink v-if="auth.isLogin":to="{ name: 'investment_survey' }"class="nav-link">투자 성향 검사</RouterLink>
    <RouterLink v-if="auth.isLogin":to="{ name: 'recommendations' }"class="nav-link">맞춤 추천</RouterLink>

    <div class="spacer"></div>

    <template v-if="auth.isLogin">
      <RouterLink :to="{ name: 'mypage' }">MyPage</RouterLink>
      <button @click="onLogout">Logout</button>
      <span>({{ auth.user?.username || "loading..." }})</span>
    </template>

    <template v-else>
      <RouterLink :to="{ name: 'login' }">Login</RouterLink>
      <RouterLink :to="{ name: 'signup' }">Signup</RouterLink>
    </template>
  </nav>
</template>

<script setup>
import { useAuthStore } from "@/stores/auth"
import { useRouter } from "vue-router"

const auth = useAuthStore()
const router = useRouter()

const onLogout = async () => {
  await auth.logout()
  router.push({ name: "main" })
}
</script>

<style scoped>
.nav { display:flex; gap:12px; align-items:center; padding:12px; }
.spacer { flex:1; }
</style>
