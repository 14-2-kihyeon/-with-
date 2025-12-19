<template>
  <div>
    <h1>로그인</h1>

    <form @submit.prevent="onSubmit">
      <div>
        <label>Username</label>
        <input v-model.trim="username" />
      </div>

      <div>
        <label>Password</label>
        <input v-model="password" type="password" />
      </div>

      <button type="submit">로그인</button>
    </form>

    <p v-if="errorMsg" style="color:red">{{ errorMsg }}</p>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()
const router = useRouter()

const username = ref("")
const password = ref("")
const errorMsg = ref("")

const onSubmit = async () => {
  errorMsg.value = ""
  try {
    await auth.login(username.value, password.value)
    router.push({ name: "mypage" })
  } catch (err) {
    errorMsg.value = JSON.stringify(err.response?.data || err.message)
  }
}
</script>
