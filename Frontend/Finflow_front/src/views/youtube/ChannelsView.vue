<template>
  <div>
    <a class="yt-back" href="javascript:void(0)" @click="goBack">&lt; 뒤로가기</a>
    <h2 class="yt-title">구독 채널</h2>

    <div v-if="channels.length === 0" class="yt-alert">구독한 채널이 없습니다.</div>

    <div style="display:flex; flex-direction:column; gap:10px;">
      <div v-for="c in channels" :key="c.channelId" class="yt-card" style="cursor:default;">
        <div class="yt-card-body" style="display:flex; justify-content:space-between; gap:10px; align-items:center;">
          <div>
            <div style="font-weight:900;">{{ c.channelTitle }}</div>
          </div>

          <div class="yt-actions" style="margin:0;">
            <!-- 채널 누르면 그 채널 기준으로 검색(검색어는 채널명 넣어줌) -->
            <button class="yt-btn" @click="goSearch(c)">영상 보기</button>
            <button class="yt-btn danger" @click="remove(c.channelId)">구독 취소</button>
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
  try { channels.value = JSON.parse(localStorage.getItem(key) || "[]") }
  catch { channels.value = [] }
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
