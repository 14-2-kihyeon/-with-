<template>
  <div>
    <h1>Main</h1>
    <p>각 기능으로 이동하세요.</p>

    <ul>
      <li><RouterLink :to="{ name: 'post_list' }">게시판</RouterLink></li>
      <li><RouterLink :to="{ name: 'deposit_list' }">정기예금</RouterLink></li>
      <li><RouterLink :to="{ name: 'saving_list' }">적금</RouterLink></li>
      <li><RouterLink :to="{ name: 'naver_news' }">네이버 뉴스</RouterLink></li>
      <li><RouterLink :to="{ name: 'bank_map' }">카카오 지도(은행찾기)</RouterLink></li>
      <li><RouterLink :to="{ name: 'mypage' }">마이페이지(로그인 필요)</RouterLink></li>
    </ul>
  </div>
</template>


<script setup>
import { useAuthStore } from "@/stores/auth"
const auth = useAuthStore()
</script>


<style scoped>

</style>