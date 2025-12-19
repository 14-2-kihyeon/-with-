<template>
  <div>
    <a class="yt-back" href="javascript:void(0)" @click="goBack">&lt; 뒤로가기</a>
    <h2 class="yt-title">나중에 볼 영상</h2>

    <div v-if="savedVideos.length === 0" class="yt-alert">저장된 영상이 없습니다.</div>

    <div class="yt-grid">
      <div v-for="v in savedVideos" :key="v.videoId">
        <div class="yt-card">
          <RouterLink :to="{ name: 'youtube_detail', params: { id: v.videoId } }">
            <img class="yt-thumb" :src="v.thumbnail" alt="thumb" />
          </RouterLink>
          <div class="yt-card-body">
            <div class="yt-card-title">{{ v.title }}</div>
            <div class="yt-card-meta">{{ v.channelTitle }}</div>

            <div class="yt-actions" style="margin-top:10px;">
              <button class="yt-btn danger" @click="remove(v.videoId)">삭제</button>
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

const router = useRouter()
const savedVideos = ref([])

const key = "savedVideos"
const load = () => {
  try { savedVideos.value = JSON.parse(localStorage.getItem(key) || "[]") }
  catch { savedVideos.value = [] }
}

const remove = (videoId) => {
  const next = savedVideos.value.filter((v) => v.videoId !== videoId)
  localStorage.setItem(key, JSON.stringify(next))
  savedVideos.value = next
}

const goBack = () => router.back()
onMounted(load)
</script>
