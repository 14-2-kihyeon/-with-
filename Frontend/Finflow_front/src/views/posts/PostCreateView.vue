<template>
  <div class="community-page">
    <!-- 헤더 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="title">글쓰기</h1>
        <p class="subtitle">금융 상품에 대한 궁금증이나 경험을 공유해주세요</p>
      </div>
      <RouterLink to="/posts" class="btn-back">
        ← 목록으로
      </RouterLink>
    </div>

    <!-- 작성 폼 카드 -->
    <div class="form-card">
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
            placeholder="궁금한 점이나 경험을 자유롭게 작성해주세요.

예시:
- 예금 vs 적금, 어떤 게 더 유리할까요?
- OO은행 정기예금 가입해보신 분 계신가요?
- 금리 비교할 때 어떤 점을 주의해야 하나요?"
            required
          ></textarea>
          <div class="form-hint">
            최소 10자 이상 작성해주세요 ({{ content.length }}자)
          </div>
        </div>

        <!-- 작성 가이드 -->
        <div class="guide-card">
          <div class="guide-icon">💡</div>
          <div class="guide-content">
            <div class="guide-title">작성 가이드</div>
            <ul class="guide-list">
              <li>구체적인 질문일수록 더 유용한 답변을 받을 수 있어요</li>
              <li>타인을 존중하는 표현을 사용해주세요</li>
              <li>개인정보는 작성하지 말아주세요</li>
            </ul>
          </div>
        </div>

        <!-- 에러 메시지 -->
        <div v-if="err" class="error-card">
          <span class="error-icon">⚠️</span>
          {{ err }}
        </div>

        <!-- 버튼 그룹 -->
        <div class="button-group">
          <RouterLink to="/posts" class="btn-secondary">
            <span class="btn-icon">✕</span>
            취소
          </RouterLink>
          <button 
            type="submit" 
            class="btn-primary"
            :disabled="!title.trim() || !content.trim() || content.length < 10"
          >
            <span class="btn-icon">✓</span>
            등록하기
          </button>
        </div>
      </form>
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
/* 페이지 래퍼 */
.community-page {
  max-width: 980px;
  margin: 0 auto;
  padding: 40px 20px;
  min-height: 100vh;
}

/* 헤더 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.header-left {
  flex: 1;
}

.title {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.subtitle {
  margin: 0;
  font-size: 15px;
  color: #64748b;
  font-weight: 400;
}

.btn-back {
  display: inline-flex;
  align-items: center;
  padding: 10px 18px;
  background: #ffffff;
  border: 1.5px solid #d1d5db;
  border-radius: 8px;
  color: #6b7280;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.15s ease;
}

.btn-back:hover {
  border-color: #9ca3af;
  background: #f8fafc;
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
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
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

/* 가이드 카드 */
.guide-card {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
}

.guide-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.guide-content {
  flex: 1;
}

.guide-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #191f28;
  margin-bottom: 8px;
}

.guide-list {
  margin: 0;
  padding-left: 20px;
  list-style: disc;
}

.guide-list li {
  font-size: 0.9rem;
  color: #4b5563;
  line-height: 1.6;
  margin-bottom: 4px;
}

.guide-list li:last-child {
  margin-bottom: 0;
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
  text-decoration: none;
}

.btn-primary {
  background: #3b82f6;
  color: #ffffff;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
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