<template>
  <section class="naver-news-list-section">
    <ul class="naver-news-list">
      <li
        v-for="n in items"
        :key="n.id"
        class="naver-news-item"
        :class="{ active: n.id === selectedId }"
        @click="$emit('select', n.id)"
      >
        <span class="naver-news-title">{{ n.title }}</span>

        <button
          class="naver-bookmark-btn"
          :class="n.is_bookmarked ? 'bookmarked' : 'not-bookmarked'"
          @click.stop="$emit('toggleBookmark', n.id)"
          title="북마크"
        >
          ★
        </button>
      </li>
    </ul>

    <p v-if="!items.length" class="naver-empty-message">
      저장된 기사가 없습니다.
    </p>
  </section>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  selectedId: { type: Number, default: null },
});
defineEmits(["select", "toggleBookmark"]);
</script>
