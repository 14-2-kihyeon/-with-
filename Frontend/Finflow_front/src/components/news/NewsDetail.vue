<template>
  <section class="naver-news-detail-section">
    <div v-if="!news" class="naver-news-detail-empty">
      <div class="empty-icon">📄</div>
      <p>기사를 선택해 주세요.</p>
    </div>

    <div v-else class="detail-content-wrapper">
      <div class="detail-header">
        <h2 class="naver-news-detail-title">{{ news.title }}</h2>
        <div class="meta-row">
          <span class="naver-news-detail-date">{{ news.pub_date || "" }}</span>
          <a
            v-if="news.link"
            :href="news.link"
            target="_blank"
            rel="noopener noreferrer"
            class="original-link"
          >
            원문 보기 →
          </a>
        </div>
      </div>

      <div class="naver-news-detail-body">
        {{ news.description || "" }}
      </div>

      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  news: { type: Object, default: null },
});
</script>