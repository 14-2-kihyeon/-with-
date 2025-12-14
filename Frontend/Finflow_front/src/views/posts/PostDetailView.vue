<template>
  <div v-if="p">
    <h1>상세</h1>

    <h2>{{ p.title }}</h2>
    <div>작성자: {{ p.user?.username }}</div>
    <p>{{ p.content }}</p>

    <div v-if="isOwner">
      <RouterLink :to="`/posts/${p.pk}/edit`">수정</RouterLink>
      <button @click="onDelete">삭제</button>
    </div>

    <hr />
    <h3>댓글</h3>

    <ul>
      <li v-for="c in p.comments" :key="c.pk">
        {{ c.user?.username }} - {{ c.content }}
        <button v-if="c.user?.pk === auth.user?.pk" @click="onDeleteComment(c.pk)">삭제</button>
      </li>
    </ul>

    <div v-if="auth.isLogin">
      <input v-model.trim="comment" placeholder="댓글 입력" />
      <button @click="onCreateComment">댓글 작성</button>
    </div>
    <div v-else>댓글 작성은 로그인 필요</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { usePostsStore } from "@/stores/posts"
import { useAuthStore } from "@/stores/auth"

const route = useRoute()
const router = useRouter()
const store = usePostsStore()
const auth = useAuthStore()

const comment = ref("")
const p = computed(() => store.post)

const isOwner = computed(() => {
  return auth.user?.pk && p.value?.user?.pk === auth.user.pk
})

onMounted(async () => {
  await store.fetchPost(route.params.pk)
})

const onDelete = async () => {
  await store.deletePost(route.params.pk)
  router.push("/posts")
}

const onCreateComment = async () => {
  if (!comment.value) return
  await store.createComment(route.params.pk, comment.value)
  comment.value = ""
  await store.fetchPost(route.params.pk)
}

const onDeleteComment = async (commentPk) => {
  await store.deleteComment(route.params.pk, commentPk)
  await store.fetchPost(route.params.pk)
}
</script>


<style scoped>

</style>