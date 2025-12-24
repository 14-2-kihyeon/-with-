<template>
  <div class="naver-news-summary">
    <div v-if="summary" class="summary-box">
      <span class="summary-label">AI 요약</span>
      <p class="naver-summary-content">{{ summary }}</p>
    </div>
    
    <button 
      v-else 
      class="naver-summary-btn" 
      :disabled="disabled || loading" 
      @click="$emit('summarize')"
    >
      <span v-if="loading">요약 생성 중...</span>
      <span v-else>🔮 AI 요약하기</span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  disabled: { type: Boolean, default: true },
  loading: { type: Boolean, default: false },
  summary: { type: String, default: "" },
});
defineEmits(["summarize"]);
</script>