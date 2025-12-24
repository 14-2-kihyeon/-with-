<template>
  <div class="yt-page">
    <header class="yt-header">
      <button class="btn-back-icon" @click="goBack" aria-label="뒤로가기">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"></polyline>
        </svg>
      </button>
      <h2 class="yt-header-title">
        <span class="yt-header-emoji">⭐</span> 구독한 채널
      </h2>
    </header>

    <div v-if="channels.length === 0" class="yt-empty">
      <div class="yt-empty-icon">📺</div>
      <div class="yt-empty-text">구독 중인 채널이 없습니다</div>
      <p style="color:#8B95A1; margin-top:8px;">자주 보는 채널을 구독하고 모아보세요.</p>
    </div>

    <div v-else style="display:flex; flex-direction:column; gap:16px;">
      <div 
        v-for="c in channels" 
        :key="c.channelId" 
        class="channel-item"
      >
        <div class="channel-info">
          <div class="channel-name">{{ c.channelTitle }}</div>
          <div class="channel-status">구독중</div>
        </div>

        <div class="yt-actions">
          <button class="yt-btn soft" @click="goSearch(c)">
            🔍 채널 영상 검색
          </button>
          <button class="yt-btn danger" @click="remove(c.channelId)">
            구독 취소
          </button>
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
  if (!confirm("구독을 취소하시겠습니까?")) return
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

<style scoped>
/* 이 페이지 전용 스타일 */
.channel-item {
  background: #ffffff;
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
  border: 1px solid #F2F4F6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  transition: transform 0.2s;
}
.channel-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.06);
}

.channel-info {
  flex: 1;
  min-width: 200px;
}
.channel-name {
  font-weight: 700;
  font-size: 18px;
  color: #191F28;
  margin-bottom: 4px;
}
.channel-status {
  font-size: 14px;
  color: #3182F6; /* Toss Blue */
  font-weight: 500;
}

@media (max-width: 600px) {
  .channel-item {
    flex-direction: column;
    align-items: flex-start;
  }
  .yt-actions {
    width: 100%;
  }
  .yt-actions button {
    flex: 1;
  }
}
</style>