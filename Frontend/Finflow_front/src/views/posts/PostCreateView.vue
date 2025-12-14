<template>
  <div>
    <h1>글쓰기</h1>

    <input v-model.trim="title" placeholder="제목" />
    <br />
    <textarea v-model="content" placeholder="내용"></textarea>
    <br />

    <button @click="onSubmit">등록</button>
    <p v-if="err" style="color:red">{{ err }}</p>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import { usePostsStore } from "@/stores/posts"

const router = useRouter()
const store = usePostsStore()

const title = ref("")
const content = ref("")
const err = ref("")

const onSubmit = async () => {
  err.value = ""
  try {
    const created = await store.createPost({ title: title.value, content: content.value })
    router.push(`/posts/${created.pk}`)
  } catch (e) {
    err.value = JSON.stringify(e.response?.data || e.message)
  }
}
</script>

<style scoped>

</style>