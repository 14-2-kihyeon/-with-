<template>
  <header class="naver-topbar">
    <div class="naver-logo">News</div>

    <div class="naver-search-area">
      <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8B95A1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
      <input
        class="naver-search-input"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        @keyup.enter="$emit('search')"
        placeholder="검색어 입력"
      />
    </div>

    <div class="naver-top-buttons">
      <button
        class="naver-top-btn"
        :class="{ active: mode === 'all' }"
        @click="$emit('setMode', 'all')"
      >
        전체
      </button>
      <button
        class="naver-top-btn"
        :class="{ active: mode === 'bookmark' }"
        @click="$emit('setMode', 'bookmark')"
      >
        북마크
      </button>
    </div>
  </header>
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: "" },
  mode: { type: String, default: "all" },
});
defineEmits(["update:modelValue", "search", "setMode"]);
</script>