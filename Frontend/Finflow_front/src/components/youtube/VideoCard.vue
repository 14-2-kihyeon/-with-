<template>
  <RouterLink class="yt-card" :to="{ name: 'youtube_detail', params: { id: video.videoId } }">
    <img class="yt-thumb" :src="video.thumbnail" alt="thumbnail" />
    <div class="yt-card-body">
      <div class="yt-card-title">{{ video.title }}</div>
      <div class="yt-card-meta">{{ video.channelTitle }}</div>
    </div>
  </RouterLink>
</template>

<script setup>
defineProps({
  video: { type: Object, required: true },
})
</script>

<style scoped>
a { text-decoration: none; color: inherit; }
</style>
