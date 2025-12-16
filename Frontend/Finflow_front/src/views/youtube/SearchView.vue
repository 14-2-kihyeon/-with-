<template>
  <div>
    <a class="yt-back" href="javascript:void(0)" @click="goBack">&lt; 뒤로가기</a>
    <h2 class="yt-title">비디오 검색</h2>

    <div class="yt-searchbar">
      <input
        placeholder="검색어를 입력하세요"
        v-model.trim="query"
        @keyup.enter="submitSearch"
      />
      <button class="yt-btn primary" @click="submitSearch" :disabled="loading || !query">
        {{ loading ? "검색중..." : "찾기" }}
      </button>
    </div>

    <!-- ✅ 추가: 검색창 밑에 2개 버튼 -->
    <div class="yt-actions" style="margin-top: 0; margin-bottom: 14px;">
      <RouterLink class="yt-btn" :to="{ name: 'youtube_saved' }">나중에 볼 영상</RouterLink>
      <RouterLink class="yt-btn" :to="{ name: 'youtube_channels' }">구독한 채널</RouterLink>
    </div>

    <div v-if="error" class="yt-alert">{{ error }}</div>

    <div class="yt-grid">
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
