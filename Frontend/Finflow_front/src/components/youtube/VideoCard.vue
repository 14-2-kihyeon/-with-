<template>
  <RouterLink class="yt-card" :to="{ name: 'youtube_detail', params: { id: video.videoId } }">
    <div class="yt-thumb-wrapper">
      <img class="yt-thumb" :src="video.thumbnail" alt="thumbnail" loading="lazy" />
    </div>
    <div class="yt-card-body">
      <div class="yt-card-title" :title="video.title">{{ video.title }}</div>
      <div class="yt-card-meta">
        <span class="channel-name">{{ video.channelTitle }}</span>
      </div>
    </div>
  </RouterLink>
</template>

<script setup>
defineProps({
  video: { type: Object, required: true },
})
</script>