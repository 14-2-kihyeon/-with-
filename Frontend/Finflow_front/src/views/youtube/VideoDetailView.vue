<template>
  <div class="yt-page">
    <div class="yt-header">
      <div class="yt-title-group">
        <h2 class="yt-title">영상 재생</h2>
      </div>
      <a class="yt-back" href="javascript:void(0)" @click="goBack">닫기</a>
    </div>

    <div v-if="loading" class="yt-loading">영상을 불러오는 중입니다...</div>
    <div v-else-if="error" class="yt-alert">⚠️ {{ error }}</div>

    <div v-else>
      <div class="yt-video-container">
        <div class="yt-video-wrapper">
          <iframe
            :src="embedUrl"
            title="YouTube video player"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen
          ></iframe>
        </div>
      </div>

      <div class="yt-info-card">
        <h1 class="yt-title" style="font-size:24px; margin-bottom:12px;">{{ video?.title }}</h1>
        
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:24px; padding-bottom:20px; border-bottom:1px solid #F2F4F6;">
          <div style="font-weight:600; font-size:16px; color:#333D4B;">
            {{ video?.channelTitle }}
            <span v-if="uploadDate" style="color:#8B95A1; font-weight:400; margin-left:8px;">{{ uploadDate }}</span>
          </div>
          
          <div class="yt-actions">
            <button class="yt-btn soft" @click="toggleSave">
              {{ isSaved ? "✅ 저장됨" : "📌 나중에 보기" }}
            </button>
            <button class="yt-btn" :class="isChannelSaved ? 'soft' : 'primary'" @click="toggleChannelSave">
              {{ isChannelSaved ? "구독중" : "구독하기" }}
            </button>
          </div>
        </div>

        <div class="yt-desc">{{ video?.description }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import {
  getYoutubeVideoDetail,
  toggleWatchLater,
  toggleChannelSubscribe,
  getWatchLaterList,
  getYoutubeSubscriptions
} from "@/api/youtube"
import { useAuthStore } from "@/stores/auth"

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const video = ref(null)
const loading = ref(false)
const error = ref("")

const videoId = computed(() => route.params.id)
const embedUrl = computed(() => `https://www.youtube.com/embed/${videoId.value}`)

const uploadDate = computed(() => {
  const p = video.value?.publishedAt
  if (!p) return ""
  return new Date(p).toLocaleDateString()
})

const isSaved = ref(false)
const isChannelSaved = ref(false)

const fallbackThumb = (id) => `https://i.ytimg.com/vi/${id}/hqdefault.jpg`

const toggleSave = async () => {
  if (!authStore.isLogin) {
    alert("로그인이 필요합니다.")
    return
  }

  try {
    const videoData = {
      video_title: video.value?.title || "",
      video_description: video.value?.description || "",
      video_thumbnail: video.value?.thumbnail || fallbackThumb(videoId.value),
      channel_title: video.value?.channelTitle || "",
      published_at: video.value?.publishedAt || "",
    }

    const res = await toggleWatchLater(videoId.value, videoData)
    isSaved.value = res.data.is_saved
    console.log(res.data.message)
  } catch (e) {
    console.error("나중에 볼 영상 토글 실패:", e)
    error.value = "저장 중 오류가 발생했습니다."
  }
}

const toggleChannelSave = async () => {
  if (!authStore.isLogin) {
    alert("로그인이 필요합니다.")
    return
  }

  const cid = video.value?.channelId
  if (!cid) return

  try {
    const channelData = {
      channel_title: video.value?.channelTitle || "",
      channel_description: video.value?.channelDescription || "",
      channel_thumbnail: video.value?.channelThumbnail || "",
    }

    const res = await toggleChannelSubscribe(cid, channelData)
    isChannelSaved.value = res.data.is_subscribed
    console.log(res.data.message)
  } catch (e) {
    console.error("채널 구독 토글 실패:", e)
    error.value = "구독 처리 중 오류가 발생했습니다."
  }
}

const checkSavedStatus = async () => {
  if (!authStore.isLogin) {
    isSaved.value = false
    isChannelSaved.value = false
    return
  }

  try {
    // 나중에 볼 영상 목록 조회
    const watchLaterRes = await getWatchLaterList()
    isSaved.value = watchLaterRes.data.some((v) => v.video_id === videoId.value)

    // 구독 채널 목록 조회
    const subscriptionsRes = await getYoutubeSubscriptions()
    const cid = video.value?.channelId
    isChannelSaved.value = !!cid && subscriptionsRes.data.some((c) => c.channel_id === cid)
  } catch (e) {
    console.error("저장 상태 확인 실패:", e)
  }
}

const fetchDetail = async () => {
  loading.value = true
  error.value = ""
  try {
    const res = await getYoutubeVideoDetail(videoId.value)
    video.value = res.data
    await checkSavedStatus()
  } catch (e) {
    error.value = "영상을 불러올 수 없습니다."
  } finally {
    loading.value = false
  }
}

watch(videoId, fetchDetail)
onMounted(fetchDetail)
const goBack = () => router.back()
</script>