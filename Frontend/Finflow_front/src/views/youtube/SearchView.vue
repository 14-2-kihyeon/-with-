<template>
  <div class="yt-page">
    <!-- 헤더 -->
    <div class="yt-header">
      <div class="yt-header-content">
        <div class="yt-title-group">
          <span class="yt-title-icon">▶️</span>
          <h2 class="yt-title">YouTube 검색</h2>
        </div>
        <a class="yt-back" href="javascript:void(0)" @click="goBack">← 뒤로가기</a>
      </div>
    </div>

    <!-- 검색바 카드 -->
    <div class="yt-search-card">
      <div class="yt-searchbar">
        <input
          placeholder="검색어를 입력하세요"
          v-model.trim="query"
          @keyup.enter="submitSearch"
        />
        <button class="yt-btn primary" @click="submitSearch" :disabled="loading || !query">
          {{ loading ? "검색중..." : "검색" }}
        </button>
      </div>

      <!-- 빠른 액세스 버튼 -->
      <div class="yt-actions" style="margin-top: 12px; margin-bottom: 0;">
        <RouterLink class="yt-btn soft" :to="{ name: 'youtube_saved' }">
          📌 나중에 볼 영상
        </RouterLink>
        <RouterLink class="yt-btn soft" :to="{ name: 'youtube_channels' }">
          ⭐ 구독한 채널
        </RouterLink>
      </div>
    </div>

    <!-- 에러 메시지 -->
    <div v-if="error" class="yt-alert">{{ error }}</div>

    <!-- 로딩 -->
    <div v-if="loading" class="yt-loading">검색 중입니다...</div>

    <!-- 빈 상태 -->
    <div v-else-if="!videos.length && query" class="yt-empty">
      <div class="yt-empty-text">검색 결과가 없습니다</div>
      <div class="yt-empty-hint">다른 검색어로 시도해보세요</div>
    </div>

    <!-- 비디오 그리드 -->
    <div v-else class="yt-grid">
      <div v-for="video in videos" :key="video.videoId">
        <VideoCard :video="video" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import VideoCard from "@/components/youtube/VideoCard.vue"
import { searchYoutube } from "@/api/youtube"

defineOptions({ name: "SearchView" })

const router = useRouter()
const route = useRoute()

const query = ref("")
const videos = ref([])
const loading = ref(false)
const error = ref("")

const submitSearch = () => {
  if (!query.value) return
  router.push({ name: "youtube_search", query: { q: query.value } })
}

watch(
  () => [route.query.q, route.query.channelId],
  async ([q, channelId]) => {
    if (typeof q !== "string" || !q.trim()) return

    query.value = q
    error.value = ""
    loading.value = true

    try {
      const res = await searchYoutube(q, typeof channelId === "string" ? channelId : "")
      videos.value = res.data
    } catch (e) {
      error.value = "검색 중 오류가 발생했습니다."
      console.error(e)
    } finally {
      loading.value = false
    }
  },
  { immediate: true }
)

const goBack = () => router.back()
</script>