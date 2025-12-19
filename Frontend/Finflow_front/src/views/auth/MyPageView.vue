<template>
  <div>
    <h1>마이페이지</h1>

    <button @click="testMe">토큰 만료 테스트(/accounts/user/)</button>
    <pre>{{ result }}</pre>

    <div v-if="auth.user">
      <p>username: {{ auth.user.username }}</p>
      <p>email: {{ auth.user.email }}</p>
    </div>
  </div>
</template>

<script setup>

import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()

</script>
