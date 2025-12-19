<template>
  <div>
    <h1>회원가입</h1>

    <form @submit.prevent="onSubmit">
      <div>
        <label>Username</label>
        <input v-model.trim="username" />
      </div>

      <!-- email이 필수로 뜨는 경우가 있어서 일단 넣어두는 걸 추천 -->
      <div>
        <label>Email</label>
        <input v-model.trim="email" type="email" />
      </div>

      <div>
        <label>Password</label>
        <input v-model="password1" type="password" />
      </div>

      <div>
        <label>Password 확인</label>
        <input v-model="password2" type="password" />
      </div>

      <button type="submit">가입</button>
    </form>

    <p v-if="errorMsg" style="color:red">{{ errorMsg }}</p>
  </div>
</template>

<script setup>
import { ref } from "vue"
import axios from "axios"
import { useRouter } from "vue-router"

const router = useRouter()
const username = ref("")
const email = ref("")
const password1 = ref("")
const password2 = ref("")
const errorMsg = ref("")

const API = "http://127.0.0.1:8000"

const onSubmit = async () => {
  errorMsg.value = ""

  const payload = {
    username: username.value,
    password1: password1.value,
    password2: password2.value,
  }
  if (email.value) payload.email = email.value

  try {
    await axios.post(`${API}/accounts/registration/`, payload)
    router.push({ name: "login" })
  } catch (err) {
    errorMsg.value = JSON.stringify(err.response?.data || err.message)
  }
}
</script>
