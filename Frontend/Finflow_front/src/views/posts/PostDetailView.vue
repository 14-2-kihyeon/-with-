<template>
  <div class="community-page">
    <!-- 헤더 -->
    <div class="page-nav">
      <RouterLink to="/posts" class="btn-back">
        ← 목록으로
      </RouterLink>
    </div>

    <!-- 로딩 -->
    <div v-if="!p" class="loading-state">
      <div class="loading-spinner">⏳</div>
      <div class="loading-text">불러오는 중...</div>
    </div>

    <!-- 게시글 상세 -->
    <div v-else>
      <!-- 게시글 카드 -->
      <div class="post-card">
        <!-- 헤더 -->
        <div class="post-header">
          <div class="header-top">
            <h1 class="post-title">{{ p.title }}</h1>

            <!-- 작성자 버튼 -->
            <div v-if="isOwner" class="post-actions">
              <RouterLink
                :to="`/posts/${p.pk}/edit`"
                class="btn-edit"
              >
                수정
              </RouterLink>
              <button
                @click="onDelete"
                class="btn-delete"
              >
                삭제
              </button>
            </div>
          </div>

          <div class="post-meta">
            <span class="meta-item">{{ p.user?.username }}</span>
            <span class="meta-divider">·</span>
            <span class="meta-item">{{ formatDate(p.created_at) }}</span>
            <span class="meta-divider">·</span>
            <span class="meta-item">댓글 {{ p.comments?.length || 0 }}개</span>
          </div>
        </div>

        <!-- 본문 -->
        <div class="post-content">
          {{ p.content }}
        </div>

        <!-- 좋아요/공유 -->
        <!-- <div class="post-footer">
          <button class="action-btn">
            <span class="action-icon">👍</span>
            좋아요
          </button>
          <button class="action-btn">
            <span class="action-icon">🔗</span>
            공유
          </button>
        </div> -->
      </div>

      <!-- 댓글 섹션 -->
      <div class="comments-card">
        <div class="comments-header">
          <h2 class="comments-title">
            댓글 {{ p.comments?.length || 0 }}개
          </h2>
        </div>

        <div class="comments-body">
          <!-- 댓글 작성 폼 (로그인 시) -->
          <div v-if="auth.isLogin" class="comment-form">
            <textarea
              v-model="comment"
              class="comment-input"
              rows="3"
              placeholder="금융 상품에 대한 의견이나 조언을 나눠주세요..."
              maxlength="200"
            ></textarea>
            <div class="comment-form-footer">
              <div class="char-count">{{ comment.length }}/200</div>
              <button
                @click="onCreateComment"
                class="btn-primary"
                :disabled="!comment.trim()"
              >
                댓글 작성
              </button>
            </div>
          </div>

          <!-- 로그인 안내 -->
          <div v-else class="login-notice">
            <span class="notice-icon">🔒</span>
            <div class="notice-text">
              댓글을 작성하려면 
              <RouterLink to="/login" class="notice-link">로그인</RouterLink>
              이 필요합니다.
            </div>
          </div>

          <!-- 댓글 목록 -->
          <div class="comments-list">
            <!-- 댓글 없을 때 -->
            <div v-if="!p.comments || p.comments.length === 0" class="empty-comments">
              <div class="empty-icon">💬</div>
              <div class="empty-text">아직 댓글이 없습니다</div>
              <div class="empty-hint">첫 댓글을 작성해보세요!</div>
            </div>

            <!-- 댓글 항목 -->
            <div
              v-for="c in p.comments"
              :key="c.pk"
              class="comment-item"
            >
              <div class="comment-header">
                <div class="comment-meta">
                  <span class="comment-username">{{ c.user?.username }}</span>
                  <span class="meta-divider">·</span>
                  <span class="comment-date">{{ formatDate(c.created_at) }}</span>
                </div>
                <!-- 댓글 삭제 버튼 -->
                <button
                  v-if="c.user?.pk === auth.user?.pk"
                  @click="onDeleteComment(c.pk)"
                  class="btn-delete-comment"
                >
                  삭제
                </button>
              </div>

              <div class="comment-content">
                {{ c.content }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
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

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '방금 전'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}분 전`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}시간 전`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}일 전`
  
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

onMounted(async () => {
  await store.fetchPost(route.params.pk)
})

const onDelete = async () => {
  if (confirm("정말 삭제하시겠습니까?")) {
    await store.deletePost(route.params.pk)
    alert("게시글이 삭제되었습니다.")
    router.push("/posts")
  }
}

const onCreateComment = async () => {
  if (!comment.value.trim()) {
    alert("댓글 내용을 입력해주세요.")
    return
  }
  
  try {
    await store.createComment(route.params.pk, comment.value)
    comment.value = ""
    await store.fetchPost(route.params.pk)
  } catch (error) {
    console.error("댓글 작성 실패:", error)
    alert("댓글 작성에 실패했습니다.")
  }
}

const onDeleteComment = async (commentPk) => {
  if (confirm("댓글을 삭제하시겠습니까?")) {
    try {
      await store.deleteComment(route.params.pk, commentPk)
      await store.fetchPost(route.params.pk)
    } catch (error) {
      console.error("댓글 삭제 실패:", error)
      alert("댓글 삭제에 실패했습니다.")
    }
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

/* 페이지 네비게이션 */
.page-nav {
  margin-bottom: 16px;
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

/* 게시글 카드 */
.post-card {
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e8eb;
  margin-bottom: 20px;
}

.post-header {
  padding: 24px 28px;
  border-bottom: 1px solid #e5e8eb;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
}

.post-title {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  line-height: 1.4;
  color: #0f172a;
  flex: 1;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-item {
  font-size: 0.9rem;
  color: #64748b;
}

.meta-divider {
  color: #cbd5e1;
  font-size: 0.9rem;
}

.post-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.btn-edit,
.btn-delete {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  text-decoration: none;
  border: 1.5px solid #d1d5db;
}

.btn-edit {
  background: #ffffff;
  color: #6b7280;
}

.btn-edit:hover {
  background: #f8fafc;
  border-color: #9ca3af;
}

.btn-delete {
  background: #ffffff;
  color: #ef4444;
  border-color: #fecaca;
}

.btn-delete:hover {
  background: #fef2f2;
  border-color: #fca5a5;
}

.post-content {
  padding: 32px 28px;
  font-size: 1.05rem;
  line-height: 1.8;
  color: #191f28;
  white-space: pre-wrap;
  word-break: break-word;
}

.post-footer {
  padding: 16px 28px;
  background: #f8fafc;
  border-top: 1px solid #e5e8eb;
  display: flex;
  gap: 10px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: #ffffff;
  border: 1.5px solid #d1d5db;
  border-radius: 8px;
  color: #6b7280;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.action-icon {
  font-size: 1rem;
}

/* 댓글 카드 */
.comments-card {
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e8eb;
}

.comments-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e8eb;
}

.comments-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #191f28;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 1.2rem;
}

.comment-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 8px;
  background: #3b82f6;
  color: #ffffff;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.comments-body {
  padding: 20px 24px;
}

/* 댓글 작성 폼 */
.comment-form {
  background: #f8fafc;
  border: 1px solid #e5e8eb;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
}

.comment-input {
  width: 100%;
  padding: 12px;
  border: 1.5px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.95rem;
  color: #191f28;
  background: #ffffff;
  resize: vertical;
  font-family: inherit;
  line-height: 1.5;
  margin-bottom: 12px;
  transition: all 0.15s ease;
}

.comment-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(0, 199, 60, 0.1);
}

.comment-input::placeholder {
  color: #9ca3af;
}

.comment-form-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.char-count {
  font-size: 0.85rem;
  color: #6b7280;
}

/* 로그인 안내 */
.login-notice {
  background: #fef3c7;
  border: 1px solid #fbbf24;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.notice-icon {
  font-size: 1.2rem;
}

.notice-text {
  font-size: 0.9rem;
  color: #92400e;
}

.notice-link {
  color: #3b82f6;
  font-weight: 600;
  text-decoration: none;
}

.notice-link:hover {
  text-decoration: underline;
}

/* 댓글 리스트 */
.comments-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-comments {
  text-align: center;
  padding: 40px 20px;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-text {
  font-size: 1rem;
  font-weight: 600;
  color: #191f28;
  margin-bottom: 4px;
}

.empty-hint {
  font-size: 0.9rem;
  color: #6b7280;
}

.comment-item {
  background: #f8fafc;
  border: 1px solid #e5e8eb;
  border-radius: 12px;
  padding: 16px;
  position: relative;
  transition: all 0.15s ease;
}

.comment-item:hover {
  background: #f1f3f5;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.comment-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.comment-username {
  font-size: 0.9rem;
  font-weight: 600;
  color: #191f28;
}

.comment-date {
  font-size: 0.85rem;
  color: #9ca3af;
}

.comment-content {
  font-size: 0.95rem;
  line-height: 1.6;
  color: #4b5563;
}

.btn-delete-comment {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  background: #ffffff;
  color: #ef4444;
  border: 1.5px solid #fecaca;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-delete-comment:hover {
  background: #fef2f2;
  border-color: #fca5a5;
}

/* 버튼 */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  background: #3b82f6;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  font-size: 0.95rem;
}

/* 반응형 */
@media (max-width: 968px) {
  .community-page {
    padding: 12px;
  }

  .post-header {
    padding: 20px;
  }

  .post-title {
    font-size: 1.3rem;
  }

  .post-content {
    padding: 24px 20px;
  }

  .post-footer,
  .comments-header,
  .comments-body {
    padding: 16px 20px;
  }
}

@media (max-width: 640px) {
  .post-title {
    font-size: 1.2rem;
  }

  .header-top {
    flex-direction: column;
  }

  .post-actions {
    width: 100%;
    flex-direction: row;
    justify-content: flex-end;
  }

  .btn-edit,
  .btn-delete {
    flex: 1;
    justify-content: center;
  }

  .comment-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>