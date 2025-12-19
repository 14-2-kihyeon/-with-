<template>
  <section class="naver-news-detail-section">
    <div v-if="!news" class="naver-news-detail-empty">
      좌측에서 기사를 선택하면 상세 내용이 여기에 표시됩니다.
    </div>

    <div v-else>
      <div class="naver-news-detail-title">{{ news.title }}</div>
      <div class="naver-news-detail-meta">{{ news.pub_date || "" }}</div>

      <a
        v-if="news.link"
        :href="news.link"
        target="_blank"
        rel="noopener noreferrer"
      >
        원문 보기
      </a>

      <hr />
      <div class="naver-news-detail-body">{{ news.description || "" }}</div>

      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  news: { type: Object, default: null },
});
</script>
