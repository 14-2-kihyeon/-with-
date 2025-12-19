<template>
  <div class="container py-5">
    <div class="row">
      <div class="col-lg-8 mx-auto">
        <!-- 뒤로가기 버튼 -->
        <div class="mb-3">
          <RouterLink to="/posts" class="btn btn-outline-secondary btn-sm">
            <i class="bi bi-arrow-left"></i> 목록으로
          </RouterLink>
        </div>

        <!-- 게시글 카드 -->
        <div v-if="p" class="card shadow-sm mb-4">
          <!-- 헤더 -->
          <div class="card-header bg-primary text-white py-3">
            <h2 class="mb-0">{{ p.title }}</h2>
          </div>

          <!-- 작성자 정보 -->
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom">
              <div class="d-flex align-items-center">
                <div class="avatar-circle bg-primary text-white me-3">
                  {{ p.user?.username?.[0]?.toUpperCase() }}
                </div>
                <div>
                  <h6 class="mb-0">{{ p.user?.username }}</h6>
                  <small class="text-muted">
                    <i class="bi bi-clock"></i>
                    {{ formatDate(p.created_at) }}
                  </small>
                </div>
              </div>

              <!-- 작성자 버튼 -->
              <div v-if="isOwner" class="btn-group">
                <RouterLink 
                  :to="`/posts/${p.pk}/edit`" 
                  class="btn btn-sm btn-outline-primary"
                >
                  <i class="bi bi-pencil"></i> 수정
                </RouterLink>
                <button 
                  @click="onDelete" 
                  class="btn btn-sm btn-outline-danger"
                >
                  <i class="bi bi-trash"></i> 삭제
                </button>
              </div>
            </div>

            <!-- 본문 -->
            <div class="post-content">
              <p class="fs-5 lh-lg">{{ p.content }}</p>
            </div>
          </div>

          <!-- 좋아요/공유 (선택사항) -->
          <div class="card-footer bg-light">
            <div class="d-flex gap-2">
              <button class="btn btn-sm btn-outline-secondary">
                <i class="bi bi-hand-thumbs-up"></i> 좋아요
              </button>
              <button class="btn btn-sm btn-outline-secondary">
                <i class="bi bi-share"></i> 공유
              </button>
            </div>
          </div>
        </div>

        <!-- 댓글 섹션 -->
        <div v-if="p" class="card shadow-sm">
          <div class="card-header bg-white py-3">
            <h4 class="mb-0">
              <i class="bi bi-chat-dots"></i>
              댓글 
              <span class="badge bg-primary ms-2">{{ p.comments?.length || 0 }}</span>
            </h4>
          </div>

          <div class="card-body">
            <!-- 댓글 작성 폼 -->
            <div v-if="auth.isLogin" class="mb-4">
              <div class="card bg-light">
                <div class="card-body">
                  <textarea
                    v-model="comment"
                    class="form-control mb-3"
                    rows="3"
                    placeholder="금융 상품에 대한 의견이나 조언을 나눠주세요..."
                    maxlength="200"
                  ></textarea>
                  <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">
                      {{ comment.length }}/200
                    </small>
                    <button 
                      @click="onCreateComment" 
                      class="btn btn-primary"
                      :disabled="!comment.trim()"
                    >
                      <i class="bi bi-send"></i> 댓글 작성
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 로그인 안내 -->
            <div v-else class="alert alert-warning d-flex align-items-center" role="alert">
              <i class="bi bi-exclamation-triangle-fill me-3"></i>
              <div>
                댓글을 작성하려면 
                <RouterLink to="/login" class="alert-link">로그인</RouterLink>
                이 필요합니다.
              </div>
            </div>

            <!-- 댓글 목록 -->
            <div class="comments-list">
              <!-- 댓글 없을 때 -->
              <div v-if="!p.comments || p.comments.length === 0" class="text-center py-5 text-muted">
                <i class="bi bi-chat display-4"></i>
                <p class="mt-3">아직 댓글이 없습니다. 첫 댓글을 작성해보세요!</p>
              </div>

              <!-- 댓글 항목 -->
              <div
                v-for="c in p.comments"
                :key="c.pk"
                class="comment-item mb-3 p-3 border rounded"
              >
                <div class="d-flex justify-content-between align-items-start">
                  <div class="flex-grow-1">
                    <div class="d-flex align-items-center mb-2">
                      <div class="avatar-circle-sm bg-secondary text-white me-2">
                        {{ c.user?.username?.[0]?.toUpperCase() }}
                      </div>
                      <div>
                        <strong>{{ c.user?.username }}</strong>
                        <small class="text-muted ms-2">
                          {{ formatDate(c.created_at) }}
                        </small>
                      </div>
                    </div>
                    <p class="mb-0">{{ c.content }}</p>
                  </div>

                  <!-- 댓글 삭제 버튼 -->
                  <button
                    v-if="c.user?.pk === auth.user?.pk"
                    @click="onDeleteComment(c.pk)"
                    class="btn btn-sm btn-outline-danger ms-2"
                  >
                    <i class="bi bi-trash"></i>
                  </button>
                </div>
              </div>
            </div>
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

// 날짜 포맷팅
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
.avatar-circle {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
}

.avatar-circle-sm {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: bold;
}

.post-content {
  font-size: 1.1rem;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.comment-item {
  background-color: #f8f9fa;
  transition: all 0.2s ease;
}

.comment-item:hover {
  background-color: #e9ecef;
  transform: translateX(5px);
}

.card {
  border: none;
  border-radius: 12px;
}

.comments-list {
  max-height: 600px;
  overflow-y: auto;
}

.form-control:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}
</style>