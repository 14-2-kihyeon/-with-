<template>
  <div class="community-page">
    <!-- 헤더 -->
    <div class="community-header">
      <div class="header-content">
        <div class="title-group">
          <span class="icon">💬</span>
          <div>
            <h1 class="title">금융 커뮤니티</h1>
            <p class="subtitle">금융 상품에 대한 궁금증을 나누고 조언을 구해보세요</p>
          </div>
        </div>
        <div v-if="auth.isLogin">
          <RouterLink to="/posts/create" class="btn-primary">
            <span class="btn-icon">✏️</span>
            글쓰기
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- 통계 카드 -->
    <div class="stats-grid">
      <div class="stat-card stat-primary">
        <div class="stat-number">{{ store.posts.length }}</div>
        <div class="stat-label">전체 게시글</div>
      </div>
      <div class="stat-card stat-success">
        <div class="stat-number">{{ totalComments }}</div>
        <div class="stat-label">전체 댓글</div>
      </div>
      <div class="stat-card stat-info">
        <div class="stat-number">{{ activeUsers }}</div>
        <div class="stat-label">활동 중인 회원</div>
      </div>
    </div>

    <!-- 게시글 목록 카드 -->
    <div class="posts-card">
      <div class="card-header">
        <h2 class="card-title">
          <span class="title-icon">📋</span>
          게시글 목록
        </h2>
        <div class="sort-buttons">
          <button
            class="sort-btn"
            :class="{ active: sortBy === 'latest' }"
            @click="sortBy = 'latest'"
          >
            최신순
          </button>
          <button
            class="sort-btn"
            :class="{ active: sortBy === 'comments' }"
            @click="sortBy = 'comments'"
          >
            댓글순
          </button>
        </div>
      </div>

      <div class="card-body">
        <!-- 빈 상태 -->
        <div v-if="store.posts.length === 0" class="empty-state">
          <div class="empty-icon">📭</div>
          <div class="empty-text">아직 작성된 게시글이 없습니다</div>
          <div class="empty-hint">첫 게시글을 작성해보세요!</div>
          <RouterLink 
            v-if="auth.isLogin" 
            to="/posts/create" 
            class="btn-primary"
            style="margin-top: 16px;"
          >
            <span class="btn-icon">✏️</span>
            첫 게시글 작성하기
          </RouterLink>
        </div>

        <!-- 게시글 리스트 -->
        <div v-else class="posts-list">
          <RouterLink
            v-for="p in sortedPosts"
            :key="p.pk"
            :to="`/posts/${p.pk}`"
            class="post-item"
          >
            <div class="post-content">
              <div class="post-header">
                <h3 class="post-title">
                  {{ p.title }}
                  <span v-if="p.comments_count > 0" class="comment-badge">
                    {{ p.comments_count }}
                  </span>
                </h3>
              </div>

              <p class="post-preview">
                {{ truncateContent(p.content, 100) }}
              </p>

              <div class="post-meta">
                <span class="meta-item">
                  <span class="meta-icon">👤</span>
                  {{ p.user?.username }}
                </span>
                <span class="meta-item">
                  <span class="meta-icon">🕐</span>
                  {{ formatDate(p.created_at) }}
                </span>
                <span class="meta-item">
                  <span class="meta-icon">💬</span>
                  댓글 {{ p.comments_count }}개
                </span>
              </div>
            </div>

            <div class="post-arrow">
              <span class="arrow-icon">→</span>
            </div>
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- 안내 메시지 -->
    <div class="info-card">
      <div class="info-icon">ℹ️</div>
      <div class="info-content">
        <div class="info-title">커뮤니티 이용 안내</div>
        <div class="info-text">
          금융 상품에 대한 궁금증과 경험을 자유롭게 공유해주세요. 
          타인을 존중하는 건강한 토론 문화를 만들어갑시다.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue"
import { usePostsStore } from "@/stores/posts"
import { useAuthStore } from "@/stores/auth"

const store = usePostsStore()
const auth = useAuthStore()
const sortBy = ref('latest')

const totalComments = computed(() => {
  return store.posts.reduce((sum, post) => sum + (post.comments_count || 0), 0)
})

const activeUsers = computed(() => {
  const users = new Set(store.posts.map(post => post.user?.username))
  return users.size
})

const sortedPosts = computed(() => {
  const posts = [...store.posts]

  if (sortBy.value === 'latest') {
    // 최신순: created_at 기준 내림차순
    return posts.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  } else {
    // 댓글순: comments_count 기준 내림차순, 같으면 최신순
    return posts.sort((a, b) => {
      if (b.comments_count !== a.comments_count) {
        return b.comments_count - a.comments_count
      }
      return new Date(b.created_at) - new Date(a.created_at)
    })
  }
})

const truncateContent = (content, maxLength) => {
  if (!content) return ''
  return content.length > maxLength 
    ? content.substring(0, maxLength) + '...' 
    : content
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '방금 전'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}분 전`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}시간 전`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}일 전`
  
  return date.toLocaleDateString('ko-KR')
}

onMounted(() => {
  store.fetchPosts()
})
</script>

<style scoped>
/* 페이지 래퍼 */
.community-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 20px;
  background: #f9fafb;
  min-height: 100vh;
}

/* 헤더 */
.community-header {
  background: #3b82f6;
  border-radius: 16px;
  padding: 24px 28px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
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
  font-size: 1.5rem;
  font-weight: 700;
  color: #ffffff;
}

.subtitle {
  margin: 4px 0 0 0;
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.9);
}

/* 통계 카드 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  border: 2px solid;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.stat-card.stat-primary {
  border-color: #3b82f6;
}

.stat-card.stat-success {
  border-color: #10b981;
}

.stat-card.stat-info {
  border-color: #3b82f6;
}

.stat-number {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-card.stat-primary .stat-number {
  color: #3b82f6;
}

.stat-card.stat-success .stat-number {
  color: #10b981;
}

.stat-card.stat-info .stat-number {
  color: #3b82f6;
}

.stat-label {
  font-size: 0.9rem;
  color: #6b7280;
}

/* 게시글 카드 */
.posts-card {
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e8eb;
  margin-bottom: 20px;
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e8eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
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

.sort-buttons {
  display: flex;
  gap: 8px;
}

.sort-btn {
  padding: 8px 16px;
  border-radius: 20px;
  border: 1.5px solid #d1d5db;
  background: #ffffff;
  color: #6b7280;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.sort-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.sort-btn.active {
  background: #3b82f6;
  color: #ffffff;
  border-color: #3b82f6;
}

.card-body {
  padding: 0;
}

/* 빈 상태 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 1.1rem;
  font-weight: 600;
  color: #191f28;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 0.95rem;
  color: #6b7280;
}

/* 게시글 리스트 */
.posts-list {
  display: flex;
  flex-direction: column;
}

.post-item {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e8eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  text-decoration: none;
  color: inherit;
  transition: all 0.15s ease;
}

.post-item:last-child {
  border-bottom: none;
}

.post-item:hover {
  background: #f8fafc;
  transform: translateX(4px);
}

.post-content {
  flex: 1;
}

.post-header {
  margin-bottom: 8px;
}

.post-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: #191f28;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.comment-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: #3b82f6;
  color: #ffffff;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
}

.post-preview {
  font-size: 0.95rem;
  color: #6b7280;
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;
  color: #9ca3af;
}

.meta-icon {
  font-size: 0.9rem;
}

.post-arrow {
  flex-shrink: 0;
}

.arrow-icon {
  font-size: 1.2rem;
  color: #d1d5db;
  transition: all 0.15s ease;
}

.post-item:hover .arrow-icon {
  color: #3b82f6;
  transform: translateX(4px);
}

/* 안내 카드 */
.info-card {
  background: #f0f9ff;
  border: 1px solid #bfdbfe;
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.info-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.info-content {
  flex: 1;
}

.info-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #191f28;
  margin-bottom: 4px;
}

.info-text {
  font-size: 0.9rem;
  color: #4b5563;
  line-height: 1.5;
}

/* 버튼 */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 12px 20px;
  background: #3b82f6;
  color: #ffffff;
  border: none;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.btn-primary:hover {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

.btn-primary:active {
  transform: translateY(0);
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
    padding: 20px;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .title {
    font-size: 1.3rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .post-item {
    padding: 16px 20px;
  }

  .post-arrow {
    display: none;
  }
}

@media (max-width: 640px) {
  .title-group .icon {
    font-size: 1.5rem;
  }

  .title {
    font-size: 1.2rem;
  }

  .subtitle {
    font-size: 0.85rem;
  }

  .stat-number {
    font-size: 1.5rem;
  }

  .post-title {
    font-size: 0.95rem;
  }

  .post-meta {
    gap: 8px;
  }

  .meta-item {
    font-size: 0.8rem;
  }
}

/* 애니메이션 */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.post-item {
  animation: slideIn 0.3s ease-out;
}
</style>