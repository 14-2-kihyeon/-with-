<template>
  <div class="community-page">
    <!-- 헤더 -->
    <div class="community-header">
      <div class="header-content">
        <div class="title-group">
          <h1 class="title">커뮤니티</h1>
          <p class="subtitle">다른 사람들과 금융 상품에 대한 경험을 공유해보세요</p>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-value">{{ store.posts.length }}</span>
            <span class="stat-label">게시글</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ totalComments }}</span>
            <span class="stat-label">댓글</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 컨트롤 바 -->
    <div class="control-bar">
      <div class="sort-tabs">
        <button
          class="sort-tab"
          :class="{ active: sortBy === 'latest' }"
          @click="sortBy = 'latest'"
        >
          최신순
        </button>
        <button
          class="sort-tab"
          :class="{ active: sortBy === 'comments' }"
          @click="sortBy = 'comments'"
        >
          댓글순
        </button>
      </div>
      <RouterLink
        v-if="auth.isLogin"
        to="/posts/create"
        class="btn-write"
      >
        글쓰기
      </RouterLink>
    </div>

    <!-- 게시글 목록 카드 -->
    <div class="posts-card">

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
                  {{ p.user?.username }}
                </span>
                <span class="meta-divider">·</span>
                <span class="meta-item">
                  {{ formatDate(p.created_at) }}
                </span>
                <span class="meta-divider">·</span>
                <span class="meta-item">
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
  max-width: 980px;
  margin: 0 auto;
  padding: 40px 20px;
  min-height: 100vh;
}

/* 헤더 */
.community-header {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
}

.title-group {
  flex: 1;
}

.title {
  margin: 0 0 8px 0;
  font-size: 32px;
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

.header-stats {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.stat-label {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
}

.stat-divider {
  width: 1px;
  height: 28px;
  background: rgba(0, 0, 0, 0.08);
}

/* 컨트롤 바 */
.control-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.sort-tabs {
  display: flex;
  gap: 4px;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 10px;
  padding: 4px;
}

.sort-tab {
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sort-tab:hover {
  color: #0f172a;
}

.sort-tab.active {
  background: #ffffff;
  color: #0f172a;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.btn-write {
  padding: 10px 20px;
  background: #0f172a;
  color: #ffffff;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-write:hover {
  background: #1e293b;
  transform: translateY(-1px);
}

/* 게시글 카드 */
.posts-card {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.06);
  margin-bottom: 24px;
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
  font-size: 0.85rem;
  color: #9ca3af;
}

.meta-divider {
  color: #d1d5db;
  font-size: 0.85rem;
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
    padding: 20px 12px;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-stats {
    width: 100%;
    justify-content: center;
  }

  .title {
    font-size: 24px;
  }

  .subtitle {
    font-size: 14px;
  }

  .post-item {
    padding: 16px 20px;
  }

  .post-arrow {
    display: none;
  }
}

@media (max-width: 640px) {
  .community-page {
    padding: 16px 12px;
  }

  .title {
    font-size: 22px;
  }

  .subtitle {
    font-size: 13px;
  }

  .stat-value {
    font-size: 18px;
  }

  .stat-label {
    font-size: 11px;
  }

  .control-bar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .btn-write {
    width: 100%;
    justify-content: center;
  }

  .post-title {
    font-size: 0.95rem;
  }

  .post-preview {
    font-size: 0.9rem;
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