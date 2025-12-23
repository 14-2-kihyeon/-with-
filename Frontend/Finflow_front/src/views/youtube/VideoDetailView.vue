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
/* 기존 스크립트 로직은 그대로 유지하되, 일부 함수만 아래처럼 수정하여 사용 */
import { computed, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { getYoutubeVideoDetail } from "@/api/youtube"

const route = useRoute()
const router = useRouter()
const video = ref(null)
const loading = ref(false)
const error = ref("")

// ... (나머지 로직 동일)

const videoId = computed(() => route.params.id)
const embedUrl = computed(() => `https://www.youtube.com/embed/${videoId.value}`)

const uploadDate = computed(() => {
  const p = video.value?.publishedAt
  if (!p) return ""
  return new Date(p).toLocaleDateString()
})

const safeParse = (key) => {
  try { return JSON.parse(localStorage.getItem(key) || "[]") } catch { return [] }
}

const savedKey = "savedVideos"
const channelsKey = "savedChannels"

const isSaved = ref(false)
const isChannelSaved = ref(false)

const syncSavedState = () => {
  const saved = safeParse(savedKey)
  isSaved.value = saved.some((v) => v.videoId === videoId.value)
}

const syncChannelSavedState = () => {
  const channels = safeParse(channelsKey)
  const cid = video.value?.channelId
  isChannelSaved.value = !!cid && channels.some((c) => c.channelId === cid)
}

const fallbackThumb = (id) => `https://i.ytimg.com/vi/${id}/hqdefault.jpg`

const toggleSave = () => {
  const saved = safeParse(savedKey)
  const idx = saved.findIndex((v) => v.videoId === videoId.value)

  if (idx >= 0) {
    saved.splice(idx, 1)
  } else {
    saved.push({
      videoId: videoId.value,
      title: video.value?.title || "",
      thumbnail: video.value?.thumbnail || fallbackThumb(videoId.value),
      channelTitle: video.value?.channelTitle || "",
    })
  }
  localStorage.setItem(savedKey, JSON.stringify(saved))
  syncSavedState()
}

const toggleChannelSave = () => {
  const cid = video.value?.channelId
  if (!cid) return
  const channels = safeParse(channelsKey)
  const idx = channels.findIndex((c) => c.channelId === cid)

  if (idx >= 0) channels.splice(idx, 1)
  else channels.push({ channelId: cid, channelTitle: video.value?.channelTitle || "" })

  localStorage.setItem(channelsKey, JSON.stringify(channels))
  syncChannelSavedState()
}

const fetchDetail = async () => {
  loading.value = true
  try {
    const res = await getYoutubeVideoDetail(videoId.value)
    video.value = res.data
    syncSavedState()
    syncChannelSavedState()
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