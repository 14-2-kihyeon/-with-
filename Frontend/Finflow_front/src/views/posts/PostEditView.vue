<template>
  <div v-if="loaded">
    <h1>수정</h1>

    <input v-model.trim="title" />
    <br />
    <textarea v-model="content"></textarea>
    <br />

    <button @click="onSubmit">저장</button>
    <p v-if="err" style="color:red">{{ err }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { usePostsStore } from "@/stores/posts"

const route = useRoute()
const router = useRouter()
const store = usePostsStore()

const title = ref("")
const content = ref("")
const err = ref("")
const loaded = ref(false)

onMounted(async () => {
  const data = await store.fetchPost(route.params.pk)
  title.value = data.title
  content.value = data.content
  loaded.value = true
})

const onSubmit = async () => {
  err.value = ""
  try {
    await store.updatePost(route.params.pk, { title: title.value, content: content.value })
    router.push(`/posts/${route.params.pk}`)
  } catch (e) {
    err.value = JSON.stringify(e.response?.data || e.message)
  }
}
</script>


<style scoped>

</style>