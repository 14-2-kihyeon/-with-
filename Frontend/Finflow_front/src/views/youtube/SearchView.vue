<template>
  <div class="yt-page">
    <header class="yt-header">
      <div class="yt-title-group">
        <span class="yt-title-icon">🔴</span>
        <h2 class="yt-title">YouTube 검색</h2>
      </div>
      <a class="yt-back" href="javascript:void(0)" @click="goBack">뒤로가기</a>
    </header>

    <div class="yt-search-card">
      <div class="yt-searchbar">
        <input
          placeholder="검색어를 입력하세요 (예: 재테크, 주식)"
          v-model.trim="query"
          @keyup.enter="submitSearch"
        />
        <button class="yt-btn primary" @click="submitSearch" :disabled="loading || !query">
          {{ loading ? "..." : "검색" }}
        </button>
      </div>

      <div class="yt-actions">
        <RouterLink class="yt-btn soft" :to="{ name: 'youtube_saved' }">
          📌 나중에 볼 영상
        </RouterLink>
        <RouterLink class="yt-btn soft" :to="{ name: 'youtube_channels' }">
          ⭐ 구독한 채널
        </RouterLink>
      </div>
    </div>

    <div v-if="error" class="yt-alert">⚠️ {{ error }}</div>

    <div v-if="loading" class="yt-loading">
      <span>영상을 찾아보고 있어요...</span>
    </div>

    <div v-else-if="!videos.length && query" class="yt-empty">
      <div class="yt-empty-icon">🔍</div>
      <div class="yt-empty-text">검색 결과가 없습니다</div>
      <p style="color:#8B95A1; margin-top:8px;">다른 키워드로 검색해보세요.</p>
    </div>

    <div v-else class="yt-grid">
      <VideoCard v-for="video in videos" :key="video.videoId" :video="video" />
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
    if (!q || (typeof q === "string" && !q.trim())) return

    query.value = q
    error.value = ""
    loading.value = true

    try {
      const res = await searchYoutube(q, typeof channelId === "string" ? channelId : "")
      videos.value = res.data || []
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