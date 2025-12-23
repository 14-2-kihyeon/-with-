<template>
  <div class="community-page">
    <!-- 헤더 -->
    <div class="community-header">
      <div class="header-content">
        <div class="title-group">
          <span class="icon">✏️</span>
          <div>
            <h1 class="title">게시글 수정</h1>
            <p class="subtitle">내용을 수정하고 저장하세요</p>
          </div>
        </div>
        <button @click="router.back()" class="btn-back">
          ← 뒤로가기
        </button>
      </div>
    </div>

    <!-- 로딩 상태 -->
    <div v-if="!loaded" class="loading-state">
      <div class="loading-spinner">⏳</div>
      <div class="loading-text">불러오는 중...</div>
    </div>

    <!-- 수정 폼 카드 -->
    <div v-else class="form-card">
      <form @submit.prevent="onSubmit">
        <!-- 제목 입력 -->
        <div class="form-group">
          <label for="title" class="form-label">
            제목 <span class="required">*</span>
          </label>
          <input
            id="title"
            v-model.trim="title"
            type="text"
            class="form-input"
            placeholder="제목을 입력하세요 (최대 10자)"
            maxlength="10"
            required
          />
          <div class="form-hint">
            {{ title.length }}/10 자
          </div>
        </div>

        <!-- 내용 입력 -->
        <div class="form-group">
          <label for="content" class="form-label">
            내용 <span class="required">*</span>
          </label>
          <textarea
            id="content"
            v-model="content"
            class="form-textarea"
            rows="12"
            placeholder="내용을 입력하세요"
            required
          ></textarea>
          <div class="form-hint">
            최소 10자 이상 작성해주세요 ({{ content.length }}자)
          </div>
        </div>

        <!-- 에러 메시지 -->
        <div v-if="err" class="error-card">
          <span class="error-icon">⚠️</span>
          {{ err }}
        </div>

        <!-- 버튼 그룹 -->
        <div class="button-group">
          <button 
            type="button"
            @click="router.back()"
            class="btn-secondary"
          >
            <span class="btn-icon">✕</span>
            취소
          </button>
          <button 
            type="submit" 
            class="btn-primary"
            :disabled="!title.trim() || !content.trim() || content.length < 10"
          >
            <span class="btn-icon">✓</span>
            저장하기
          </button>
        </div>
      </form>
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
/* 페이지 래퍼 */
.community-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  background: #f9fafb;
  min-height: 100vh;
}

/* 헤더 */
.community-header {
  background: #00C73C;
  border-radius: 16px;
  padding: 20px 28px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 199, 60, 0.15);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-group .icon {
  font-size: 2rem;
}

.title {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
  color: #ffffff;
}

.subtitle {
  margin: 4px 0 0 0;
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.9);
}

.btn-back {
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-back:hover {
  background: rgba(255, 255, 255, 0.25);
}

/* 로딩 상태 */
.loading-state {
  text-align: center;
  padding: 80px 20px;
}

.loading-spinner {
  font-size: 3rem;
  margin-bottom: 16px;
  animation: pulse 1.5s ease-in-out infinite;
}

.loading-text {
  font-size: 1rem;
  color: #6b7280;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 폼 카드 */
.form-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e8eb;
}

/* 폼 그룹 */
.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 0.95rem;
  font-weight: 600;
  color: #191f28;
  margin-bottom: 8px;
}

.required {
  color: #ef4444;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1.5px solid #d1d5db;
  border-radius: 10px;
  font-size: 0.95rem;
  color: #191f28;
  background: #ffffff;
  transition: all 0.15s ease;
  font-family: inherit;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #00C73C;
  box-shadow: 0 0 0 3px rgba(0, 199, 60, 0.1);
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: #9ca3af;
}

.form-textarea {
  resize: vertical;
  min-height: 300px;
  line-height: 1.6;
}

.form-hint {
  margin-top: 6px;
  font-size: 0.85rem;
  color: #6b7280;
}

/* 에러 카드 */
.error-card {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 20px;
  color: #991b1b;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-icon {
  font-size: 1.1rem;
}

/* 버튼 그룹 */
.button-group {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.btn-primary,
.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 13px 24px;
  border: none;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-primary {
  background: #00C73C;
  color: #ffffff;
  box-shadow: 0 2px 4px rgba(0, 199, 60, 0.2);
}

.btn-primary:hover:not(:disabled) {
  background: #00A832;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 199, 60, 0.3);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-secondary {
  background: #ffffff;
  color: #6b7280;
  border: 1.5px solid #d1d5db;
}

.btn-secondary:hover {
  border-color: #9ca3af;
  background: #f8fafc;
}

.btn-icon {
  font-size: 1rem;
}

/* 반응형 */
@media (max-width: 968px) {
  .community-page {
    padding: 12px;
  }

  .community-header {
    padding: 16px 20px;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .title {
    font-size: 1.2rem;
  }

  .form-card {
    padding: 24px 20px;
  }

  .button-group {
    flex-direction: column;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 640px) {
  .title-group .icon {
    font-size: 1.5rem;
  }

  .form-card {
    padding: 20px 16px;
  }

  .form-textarea {
    min-height: 250px;
  }
}
</style>