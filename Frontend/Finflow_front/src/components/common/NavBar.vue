<template>
  <nav style="display:flex; gap:12px; align-items:center;">
    <RouterLink to="/">Home</RouterLink>
    <RouterLink to="/posts">Posts</RouterLink>

    <template v-if="auth.isLogin">
      <RouterLink to="/mypage">MyPage</RouterLink>
      <button @click="onLogout">Logout</button>
      <span>({{ auth.user?.username || "loading..." }})</span>
    </template>

    <template v-else>
      <RouterLink to="/login">Login</RouterLink>
      <RouterLink to="/signup">Signup</RouterLink>
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
  router.push("/")
}
</script>


<style scoped>

</style>
