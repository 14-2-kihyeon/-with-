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
          @click.stop="$emit('toggleBookmark', n.id)"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            :stroke="n.is_bookmarked ? '#3182F6' : '#B0B8C1'"
            :fill="n.is_bookmarked ? '#3182F6' : 'none'"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
          </svg>
        </button>
      </li>
    </ul>

    <p v-if="!items.length" class="naver-empty-message">
      표시할 기사가 없어요.
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