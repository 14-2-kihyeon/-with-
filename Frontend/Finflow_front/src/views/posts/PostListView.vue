<template>
  <div>
    <h1>게시글 목록</h1>

    <div v-if="auth.isLogin">
      <RouterLink to="/posts/create">+ 글쓰기</RouterLink>
    </div>

    <hr />

    <div v-for="p in store.posts" :key="p.pk" style="margin-bottom:12px;">
      <RouterLink :to="`/posts/${p.pk}`">
        <b>{{ p.title }}</b>
      </RouterLink>
      <div>작성자: {{ p.user?.username }}</div>
      <div>댓글: {{ p.comments_count }}</div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from "vue"
import { usePostsStore } from "@/stores/posts"
import { useAuthStore } from "@/stores/auth"

const store = usePostsStore()
const auth = useAuthStore()

onMounted(() => {
  store.fetchPosts()
})
</script>


<style scoped>

</style>