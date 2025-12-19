<template>
  <div class="container py-5">
    <div class="row">
      <div class="col-lg-8 mx-auto">
        <!-- 헤더 -->
        <div class="mb-4">
          <h1 class="display-5 fw-bold">
            <i class="bi bi-pencil"></i> 게시글 수정
          </h1>
          <p class="text-muted">내용을 수정하고 저장하세요</p>
        </div>

        <!-- 수정 폼 -->
        <div v-if="loaded" class="card shadow-sm">
          <div class="card-body p-4">
            <form @submit.prevent="onSubmit">
              <!-- 제목 입력 -->
              <div class="mb-4">
                <label for="title" class="form-label fw-bold">
                  제목 <span class="text-danger">*</span>
                </label>
                <input
                  id="title"
                  v-model.trim="title"
                  type="text"
                  class="form-control form-control-lg"
                  placeholder="제목을 입력하세요 (최대 10자)"
                  maxlength="10"
                  required
                />
                <div class="form-text">
                  {{ title.length }}/10 자
                </div>
              </div>

              <!-- 내용 입력 -->
              <div class="mb-4">
                <label for="content" class="form-label fw-bold">
                  내용 <span class="text-danger">*</span>
                </label>
                <textarea
                  id="content"
                  v-model="content"
                  class="form-control"
                  rows="12"
                  placeholder="내용을 입력하세요"
                  required
                ></textarea>
                <div class="form-text">
                  최소 10자 이상 작성해주세요
                </div>
              </div>

              <!-- 에러 메시지 -->
              <div v-if="err" class="alert alert-danger" role="alert">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                {{ err }}
              </div>

              <!-- 버튼 -->
              <div class="d-flex gap-2 justify-content-end">
                <button 
                  type="button"
                  @click="router.back()"
                  class="btn btn-lg btn-outline-secondary"
                >
                  <i class="bi bi-x-circle"></i> 취소
                </button>
                <button 
                  type="submit" 
                  class="btn btn-lg btn-primary"
                  :disabled="!title.trim() || !content.trim() || content.length < 10"
                >
                  <i class="bi bi-check-circle"></i> 저장하기
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- 로딩 -->
        <div v-else class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">로딩 중...</span>
          </div>
        </div>
      </div>
    </div>
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
  try {
    const data = await store.fetchPost(route.params.pk)
    title.value = data.title
    content.value = data.content
    loaded.value = true
  } catch (error) {
    console.error("게시글 로딩 실패:", error)
    alert("게시글을 불러올 수 없습니다.")
    router.push("/posts")
  }
})

const onSubmit = async () => {
  err.value = ""
  
  // 유효성 검사
  if (!title.value.trim()) {
    err.value = "제목을 입력해주세요."
    return
  }
  
  if (!content.value.trim()) {
    err.value = "내용을 입력해주세요."
    return
  }
  
  if (content.value.length < 10) {
    err.value = "내용을 최소 10자 이상 작성해주세요."
    return
  }
  
  try {
    await store.updatePost(route.params.pk, { 
      title: title.value, 
      content: content.value 
    })
    
    alert("게시글이 수정되었습니다!")
    router.push(`/posts/${route.params.pk}`)
  } catch (e) {
    console.error("수정 실패:", e)
    err.value = e.response?.data?.detail || "게시글 수정에 실패했습니다."
  }
}
</script>

<style scoped>
.card {
  border: none;
  border-radius: 12px;
}

.form-control:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

textarea.form-control {
  resize: vertical;
  min-height: 300px;
}

.btn-lg {
  padding: 0.75rem 1.5rem;
  font-size: 1.1rem;
}
</style>