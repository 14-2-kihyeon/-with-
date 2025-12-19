<template>
  <section class="naver-news-list-section">
    <ul class="naver-news-list">
      <li
        v-for="n in news"
        :key="n.id"
        class="naver-news-item"
        :class="{ active: n.id === selectedId }"
        @click="$emit('select', n.id)"
      >
        <span class="naver-news-title">{{ n.title }}</span>
        <button
          class="naver-bookmark-btn"
          :class="n.is_bookmarked ? 'bookmarked' : 'not-bookmarked'"
          @click.stop="$emit('toggle', n.id)"
          aria-label="bookmark"
        >
          ★
        </button>
      </li>
    </ul>

    <p v-if="!news.length" class="naver-empty-message">
      아직 저장된 기사가 없습니다.
    </p>
  </section>
</template>

<script setup>
defineProps({
  news: { type: Array, default: () => [] },
  selectedId: { type: [Number, null], default: null },
})
defineEmits(["select", "toggle"])
</script>
