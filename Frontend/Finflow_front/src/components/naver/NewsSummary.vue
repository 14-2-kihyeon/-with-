<template>
  <div class="naver-news-summary">
    <button class="naver-summary-btn" :disabled="disabled" @click="$emit('summarize')">
      {{ loading ? "요약 중..." : "요약 보기" }}
    </button>
    <div class="naver-summary-content">{{ summary }}</div>
  </div>
</template>

<script setup>
defineProps({
  summary: { type: String, default: "" },
  disabled: { type: Boolean, default: true },
  loading: { type: Boolean, default: false },
})
defineEmits(["summarize"])
</script>
