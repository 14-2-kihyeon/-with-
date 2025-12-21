<template>
  <div>
    <ul v-if="items?.length" class="list">
      <li v-for="(n, idx) in items" :key="idx" class="item">
        <a class="title" :href="n.link || n.originallink" target="_blank" rel="noopener">
          {{ n.title }}
        </a>
        <p class="desc" v-if="n.description">{{ n.description }}</p>
        <p class="meta">
          <span v-if="n.published_at">{{ n.published_at }}</span>
          <span v-if="n.source"> · {{ n.source }}</span>
        </p>
      </li>
    </ul>
    <p v-else class="empty">뉴스가 없습니다. (refresh로 강제 갱신해봐)</p>
  </div>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
})
</script>

<style scoped>
.list { list-style: none; padding: 0; margin: 12px 0 0; display: grid; gap: 10px; }
.item { padding: 12px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.08); background: rgba(255,255,255,0.6); }
.title { font-weight: 900; text-decoration: none; display: inline-block; }
.desc { margin: 8px 0 0; opacity: 0.8; line-height: 1.5; }
.meta { margin-top: 8px; opacity: 0.7; font-size: 12px; }
.empty { margin-top: 10px; opacity: 0.75; }
</style>
