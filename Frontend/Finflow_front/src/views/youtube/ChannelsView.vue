<template>
  <div class="yt-page">
    <!-- 헤더 -->
    <div class="yt-header">
      <div class="yt-header-content">
        <div class="yt-title-group">
          <span class="yt-title-icon">⭐</span>
          <h2 class="yt-title">구독 채널</h2>
        </div>
        <a class="yt-back" href="javascript:void(0)" @click="goBack">← 뒤로가기</a>
      </div>
    </div>

    <!-- 빈 상태 -->
    <div v-if="channels.length === 0" class="yt-empty">
      <div class="yt-empty-text">구독한 채널이 없습니다</div>
      <div class="yt-empty-hint">관심있는 채널을 구독해보세요</div>
    </div>

    <!-- 채널 리스트 -->
    <div v-else style="display:flex; flex-direction:column; gap:12px;">
      <div 
        v-for="c in channels" 
        :key="c.channelId" 
        style="background:#ffffff; border-radius:12px; padding:16px 20px; box-shadow:0 1px 3px rgba(0,0,0,0.04); border:1px solid #e5e8eb;"
      >
        <div style="display:flex; justify-content:space-between; gap:16px; align-items:center; flex-wrap:wrap;">
          <div style="flex:1; min-width:200px;">
            <div style="font-weight:700; font-size:1.05rem; color:#191f28; margin-bottom:4px;">
              {{ c.channelTitle }}
            </div>
            <div style="font-size:0.85rem; color:#6b7280;">
              구독중인 채널
            </div>
          </div>

          <div class="yt-actions" style="margin:0; flex-shrink:0;">
            <button class="yt-btn soft" @click="goSearch(c)">
              🔍 영상 보기
            </button>
            <button class="yt-btn danger" @click="remove(c.channelId)">
              🗑️ 구독 취소
            </button>
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
const channels = ref([])
const key = "savedChannels"

const load = () => {
  try { 
    channels.value = JSON.parse(localStorage.getItem(key) || "[]") 
  } catch { 
    channels.value = [] 
  }
}

const remove = (channelId) => {
  const next = channels.value.filter((c) => c.channelId !== channelId)
  localStorage.setItem(key, JSON.stringify(next))
  channels.value = next
}

const goSearch = (c) => {
  router.push({
    name: "youtube_search",
    query: { q: c.channelTitle || " ", channelId: c.channelId },
  })
}

const goBack = () => router.back()

onMounted(load)
</script>