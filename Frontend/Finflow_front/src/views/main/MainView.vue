<template>
  <div>
    <h1>Finflow 메인</h1>

    <p v-if="auth.isLogin">
      로그인: {{ auth.user?.username || "loading..." }}
    </p>
    <p v-else>
      로그인 필요 기능이 있습니다.
    </p>

    <hr />

    <h2>바로가기</h2>
    <ul>
      <li>
        <RouterLink to="/posts">게시판(Posts)</RouterLink>
      </li>

      <!-- 앞으로 합칠 앱들 자리 -->
      <li>
        <span>예금/적금(Finances) - 준비중</span>
      </li>
      <li>
        <span>뉴스(NaverSearch) - 준비중</span>
      </li>
      <li>
        <span>카카오맵(은행 찾기) - 준비중</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { useAuthStore } from "@/stores/auth"
const auth = useAuthStore()
</script>


<style scoped>

</style>