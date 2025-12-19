<template>
  <div class="container py-5">
    <!-- 헤더 -->
    <div class="row mb-4">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <h1 class="display-5 fw-bold mb-2">💬 금융 커뮤니티</h1>
            <p class="text-muted">금융 상품에 대한 궁금증을 나누고 조언을 구해보세요</p>
          </div>
          <div v-if="auth.isLogin">
            <RouterLink 
              to="/posts/create" 
              class="btn btn-primary btn-lg"
            >
              <i class="bi bi-pencil-square"></i> 글쓰기
            </RouterLink>
          </div>
        </div>
      </div>
    </div>

    <!-- 통계 카드 -->
    <div class="row mb-4">
      <div class="col-md-4">
        <div class="card border-primary">
          <div class="card-body text-center">
            <h3 class="text-primary mb-0">{{ store.posts.length }}</h3>
            <p class="text-muted mb-0">전체 게시글</p>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card border-success">
          <div class="card-body text-center">
            <h3 class="text-success mb-0">{{ totalComments }}</h3>
            <p class="text-muted mb-0">전체 댓글</p>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card border-info">
          <div class="card-body text-center">
            <h3 class="text-info mb-0">{{ activeUsers }}</h3>
            <p class="text-muted mb-0">활동 중인 회원</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 게시글 목록 -->
    <div class="row">
      <div class="col-12">
        <div class="card shadow-sm">
          <div class="card-header bg-white py-3">
            <div class="d-flex justify-content-between align-items-center">
              <h5 class="mb-0">
                <i class="bi bi-list-ul"></i> 게시글 목록
              </h5>
              <div class="btn-group" role="group">
                <button 
                  type="button" 
                  class="btn btn-sm btn-outline-secondary active"
                >
                  최신순
                </button>
                <button 
                  type="button" 
                  class="btn btn-sm btn-outline-secondary"
                >
                  댓글순
                </button>
              </div>
            </div>
          </div>
          
          <div class="card-body p-0">
            <!-- 게시글 없을 때 -->
            <div v-if="store.posts.length === 0" class="text-center py-5">
              <i class="bi bi-inbox display-1 text-muted"></i>
              <p class="text-muted mt-3">아직 작성된 게시글이 없습니다.</p>
              <RouterLink 
                v-if="auth.isLogin" 
                to="/posts/create" 
                class="btn btn-primary"
              >
                첫 게시글 작성하기
              </RouterLink>
            </div>

            <!-- 게시글 목록 -->
            <div class="list-group list-group-flush">
              <RouterLink
                v-for="p in store.posts"
                :key="p.pk"
                :to="`/posts/${p.pk}`"
                class="list-group-item list-group-item-action py-4"
              >
                <div class="d-flex w-100 justify-content-between align-items-start">
                  <div class="flex-grow-1">
                    <!-- 제목 -->
                    <h5 class="mb-2">
                      {{ p.title }}
                      <span 
                        v-if="p.comments_count > 0" 
                        class="badge bg-primary ms-2"
                      >
                        {{ p.comments_count }}
                      </span>
                    </h5>
                    
                    <!-- 내용 미리보기 -->
                    <p class="mb-2 text-muted">
                      {{ truncateContent(p.content, 100) }}
                    </p>
                    
                    <!-- 메타 정보 -->
                    <div class="d-flex align-items-center gap-3 text-muted small">
                      <span>
                        <i class="bi bi-person-circle"></i>
                        {{ p.user?.username }}
                      </span>
                      <span>
                        <i class="bi bi-clock"></i>
                        {{ formatDate(p.created_at) }}
                      </span>
                      <span>
                        <i class="bi bi-chat-dots"></i>
                        댓글 {{ p.comments_count }}개
                      </span>
                    </div>
                  </div>
                  
                  <!-- 오른쪽 화살표 -->
                  <div class="ms-3">
                    <i class="bi bi-chevron-right text-muted"></i>
                  </div>
                </div>
              </RouterLink>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 하단 안내 -->
    <div class="row mt-4">
      <div class="col-12">
        <div class="alert alert-info d-flex align-items-center" role="alert">
          <i class="bi bi-info-circle-fill me-3 fs-4"></i>
          <div>
            <strong>커뮤니티 이용 안내</strong>
            <p class="mb-0">
              금융 상품에 대한 궁금증과 경험을 자유롭게 공유해주세요. 
              타인을 존중하는 건강한 토론 문화를 만들어갑시다.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue"
import { usePostsStore } from "@/stores/posts"
import { useAuthStore } from "@/stores/auth"

const store = usePostsStore()
const auth = useAuthStore()

// 전체 댓글 수 계산
const totalComments = computed(() => {
  return store.posts.reduce((sum, post) => sum + (post.comments_count || 0), 0)
})

// 활동 중인 회원 수 (중복 제거)
const activeUsers = computed(() => {
  const users = new Set(store.posts.map(post => post.user?.username))
  return users.size
})

// 내용 자르기
const truncateContent = (content, maxLength) => {
  if (!content) return ''
  return content.length > maxLength 
    ? content.substring(0, maxLength) + '...' 
    : content
}

// 날짜 포맷팅
const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  
  // 1분 미만
  if (diff < 60000) {
    return '방금 전'
  }
  // 1시간 미만
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}분 전`
  }
  // 24시간 미만
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}시간 전`
  }
  // 7일 미만
  if (diff < 604800000) {
    return `${Math.floor(diff / 86400000)}일 전`
  }
  // 그 이상
  return date.toLocaleDateString('ko-KR')
}

onMounted(() => {
  store.fetchPosts()
})
</script>

<style scoped>
.list-group-item {
  border-left: none;
  border-right: none;
  transition: all 0.2s ease;
}

.list-group-item:hover {
  background-color: #f8f9fa;
  transform: translateX(5px);
}

.list-group-item:first-child {
  border-top: none;
}

.card {
  border: none;
  border-radius: 12px;
}

.card-header {
  border-bottom: 2px solid #f0f0f0;
}

.btn-group .btn {
  border-radius: 20px;
}

.btn-group .btn:not(:last-child) {
  margin-right: 0.5rem;
}

.gap-3 {
  gap: 1rem !important;
}
</style>