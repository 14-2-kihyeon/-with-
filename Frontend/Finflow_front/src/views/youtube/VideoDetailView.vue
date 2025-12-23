<template>
  <div class="yt-page">
    <!-- 헤더 -->
    <div class="yt-header">
      <div class="yt-header-content">
        <div class="yt-title-group">
          <span class="yt-title-icon">▶️</span>
          <h2 class="yt-title">동영상 재생</h2>
        </div>
        <a class="yt-back" href="javascript:void(0)" @click="goBack">← 뒤로가기</a>
      </div>
    </div>

    <!-- 로딩/에러 상태 -->
    <div v-if="loading" class="yt-loading">불러오는 중...</div>
    <div v-else-if="error" class="yt-alert">{{ error }}</div>

    <!-- 비디오 상세 -->
    <div v-else>
      <!-- 비디오 플레이어 -->
      <div class="yt-video-container">
        <div class="yt-video-wrapper">
          <iframe
            :src="embedUrl"
            title="YouTube video player"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowfullscreen
          ></iframe>
        </div>
      </div>

      <!-- 비디오 정보 카드 -->
      <div style="background:#ffffff; border-radius:16px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,0.06); border:1px solid #e5e8eb; margin-bottom:16px;">
        <h2 class="yt-title" style="color:#191f28; margin:0 0 12px 0; font-size:1.3rem;">
          {{ video?.title }}
        </h2>
        
        <div class="yt-card-meta" style="margin-bottom:16px; padding-bottom:16px; border-bottom:1px solid #e5e8eb;">
          {{ video?.channelTitle }}
          <span v-if="uploadDate" style="margin-left:12px; color:#9ca3af;">
            · {{ uploadDate }}
          </span>
        </div>

        <!-- 설명 -->
        <div class="yt-desc">{{ video?.description }}</div>

        <!-- 액션 버튼 -->
        <div class="yt-actions">
          <button 
            class="yt-btn soft" 
            :class="{ 'opacity-50': isSaved }" 
            @click="toggleSave"
          >
            {{ isSaved ? "📌 저장됨" : "📌 나중에 보기" }}
          </button>

          <button 
            class="yt-btn warn" 
            :class="{ 'opacity-50': isChannelSaved }" 
            @click="toggleChannelSave"
          >
            {{ isChannelSaved ? "⭐ 구독중" : "⭐ 채널 구독" }}
          </button>

          <RouterLink class="yt-btn soft" :to="{ name: 'youtube_saved' }">
            📋 저장 목록
          </RouterLink>
          
          <RouterLink class="yt-btn soft" :to="{ name: 'youtube_channels' }">
            📺 구독 채널
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { getYoutubeVideoDetail } from "@/api/youtube"

const route = useRoute()
const router = useRouter()

const video = ref(null)
const loading = ref(false)
const error = ref("")

const videoId = computed(() => route.params.id)
const embedUrl = computed(() => `https://www.youtube.com/embed/${videoId.value}`)

const uploadDate = computed(() => {
  const p = video.value?.publishedAt
  if (!p) return ""
  return new Date(p).toISOString().slice(0, 10)
})

// localStorage helpers
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
  const ctitle = video.value?.channelTitle || ""
  if (!cid) return

  const channels = safeParse(channelsKey)
  const idx = channels.findIndex((c) => c.channelId === cid)

  if (idx >= 0) channels.splice(idx, 1)
  else channels.push({ channelId: cid, channelTitle: ctitle })

  localStorage.setItem(channelsKey, JSON.stringify(channels))
  syncChannelSavedState()
}

const fetchDetail = async () => {
  loading.value = true
  error.value = ""
  try {
    const res = await getYoutubeVideoDetail(videoId.value)
    video.value = res.data
    syncSavedState()
    syncChannelSavedState()
  } catch (e) {
    error.value = "상세 정보를 불러오지 못했습니다. (백엔드 URL 확인)"
    console.error(e)
  } finally {
    loading.value = false
  }
}

watch(videoId, () => fetchDetail())

const goBack = () => router.back()

onMounted(fetchDetail)
</script>