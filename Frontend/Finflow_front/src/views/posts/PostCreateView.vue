<template>
  <div class="container py-5">
    <div class="row">
      <div class="col-lg-8 mx-auto">
        <!-- 헤더 -->
        <div class="mb-4">
          <h1 class="display-5 fw-bold">
            <i class="bi bi-pencil-square"></i> 글쓰기
          </h1>
          <p class="text-muted">금융 상품에 대한 궁금증이나 경험을 공유해주세요</p>
        </div>

        <!-- 작성 폼 -->
        <div class="card shadow-sm">
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
                  placeholder="궁금한 점이나 경험을 자유롭게 작성해주세요.

예시:
- 예금 vs 적금, 어떤 게 더 유리할까요?
- OO은행 정기예금 가입해보신 분 계신가요?
- 금리 비교할 때 어떤 점을 주의해야 하나요?"
                  required
                ></textarea>
                <div class="form-text">
                  최소 10자 이상 작성해주세요
                </div>
              </div>

              <!-- 작성 가이드 -->
              <div class="alert alert-info d-flex align-items-start" role="alert">
                <i class="bi bi-info-circle-fill me-3 mt-1"></i>
                <div>
                  <strong>작성 가이드</strong>
                  <ul class="mb-0 mt-2">
                    <li>구체적인 질문일수록 더 유용한 답변을 받을 수 있어요</li>
                    <li>타인을 존중하는 표현을 사용해주세요</li>
                    <li>개인정보는 작성하지 말아주세요</li>
                  </ul>
                </div>
              </div>

              <!-- 에러 메시지 -->
              <div v-if="err" class="alert alert-danger" role="alert">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                {{ err }}
              </div>

              <!-- 버튼 -->
              <div class="d-flex gap-2 justify-content-end">
                <RouterLink to="/posts" class="btn btn-lg btn-outline-secondary">
                  <i class="bi bi-x-circle"></i> 취소
                </RouterLink>
                <button 
                  type="submit" 
                  class="btn btn-lg btn-primary"
                  :disabled="!title.trim() || !content.trim() || content.length < 10"
                >
                  <i class="bi bi-check-circle"></i> 등록하기
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
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
    const created = await store.createPost({ 
      title: title.value, 
      content: content.value 
    })
    
    alert("게시글이 작성되었습니다!")
    router.push(`/posts/${created.pk}`)
  } catch (e) {
    console.error("게시글 작성 실패:", e)
    err.value = e.response?.data?.detail || "게시글 작성에 실패했습니다."
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

ul {
  padding-left: 1.5rem;
}

ul li {
  margin-bottom: 0.5rem;
}
</style>