<template>
  <div class="yt-page">
    <!-- 헤더 -->
    <header class="yt-header">
      <button class="btn-back-icon" @click="goBack" aria-label="뒤로가기">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"></polyline>
        </svg>
      </button>
      <h2 class="yt-header-title">
        <span class="yt-header-emoji">📌</span> 나중에 볼 영상
      </h2>
    </header>

    <!-- 빈 상태 -->
    <div v-if="savedVideos.length === 0" class="yt-empty">
      <div class="yt-empty-text">저장된 영상이 없습니다</div>
      <div class="yt-empty-hint">관심있는 영상을 저장해보세요</div>
    </div>

    <!-- 저장된 비디오 그리드 -->
    <div v-else class="yt-grid">
      <div v-for="v in savedVideos" :key="v.videoId">
        <div class="yt-card">
          <RouterLink :to="{ name: 'youtube_detail', params: { id: v.videoId } }">
            <img class="yt-thumb" :src="v.thumbnail" alt="thumb" />
          </RouterLink>
          <div class="yt-card-body">
            <div class="yt-card-title">{{ v.title }}</div>
            <div class="yt-card-meta">{{ v.channelTitle }}</div>

            <div class="yt-actions" style="margin-top:12px;">
              <RouterLink 
                class="yt-btn soft" 
                :to="{ name: 'youtube_detail', params: { id: v.videoId } }"
              >
                ▶️ 재생
              </RouterLink>
              <button class="yt-btn danger" @click="remove(v.videoId)">
                🗑️ 삭제
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()
const savedVideos = ref([])

const key = "savedVideos"

const load = () => {
  try { 
    savedVideos.value = JSON.parse(localStorage.getItem(key) || "[]") 
  } catch { 
    savedVideos.value = [] 
  }
}

const remove = (videoId) => {
  const next = savedVideos.value.filter((v) => v.videoId !== videoId)
  localStorage.setItem(key, JSON.stringify(next))
  savedVideos.value = next
}

const goBack = () => router.back()

onMounted(load)
</script>