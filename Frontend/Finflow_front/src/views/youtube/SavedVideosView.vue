<template>
  <div class="yt-page">
    <!-- Alert Modal -->
    <AlertModal
      v-model="showAlert"
      :icon="alertConfig.icon"
      :title="alertConfig.title"
      :message="alertConfig.message"
      :confirm-text="alertConfig.confirmText"
      @confirm="alertConfig.onConfirm"
    />

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

    <!-- 로딩 상태 -->
    <div v-if="loading" class="yt-loading">
      <span>영상 목록을 불러오는 중...</span>
    </div>

    <!-- 빈 상태 -->
    <div v-else-if="savedVideos.length === 0" class="yt-empty">
      <div class="yt-empty-text">저장된 영상이 없습니다</div>
      <div class="yt-empty-hint">관심있는 영상을 저장해보세요</div>
    </div>

    <!-- 저장된 비디오 그리드 -->
    <div v-else class="yt-grid">
      <div v-for="v in savedVideos" :key="v.video_id">
        <div class="yt-card">
          <RouterLink :to="{ name: 'youtube_detail', params: { id: v.video_id } }">
            <img class="yt-thumb" :src="v.video_thumbnail" alt="thumb" />
          </RouterLink>
          <div class="yt-card-body">
            <div class="yt-card-title">{{ v.video_title }}</div>
            <div class="yt-card-meta">{{ v.channel_title }}</div>

            <div class="yt-actions" style="margin-top:12px;">
              <RouterLink
                class="yt-btn soft"
                :to="{ name: 'youtube_detail', params: { id: v.video_id } }"
              >
                ▶️ 재생
              </RouterLink>
              <button class="yt-btn danger" @click="remove(v.video_id)">
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
import { getWatchLaterList, toggleWatchLater } from "@/api/youtube"
import AlertModal from "@/components/common/AlertModal.vue"
import { useAlert } from "@/composables/useAlert"

const router = useRouter()
const savedVideos = ref([])
const loading = ref(false)

// Alert composable
const { showAlert, alertConfig, error } = useAlert()

const load = async () => {
  loading.value = true
  try {
    const res = await getWatchLaterList()
    savedVideos.value = res.data
  } catch (error) {
    console.error("나중에 볼 영상 목록 조회 실패:", error)
    savedVideos.value = []
  } finally {
    loading.value = false
  }
}

const remove = async (videoId) => {
  try {
    const videoData = savedVideos.value.find(v => v.video_id === videoId)
    await toggleWatchLater(videoId, {
      video_title: videoData?.video_title || "",
      video_description: videoData?.video_description || "",
      video_thumbnail: videoData?.video_thumbnail || "",
      channel_title: videoData?.channel_title || "",
      published_at: videoData?.published_at || "",
    })
    savedVideos.value = savedVideos.value.filter((v) => v.video_id !== videoId)
  } catch (err) {
    console.error("영상 삭제 실패:", err)
    error("영상 삭제에 실패했습니다.")
  }
}

const goBack = () => router.back()

onMounted(load)
</script>