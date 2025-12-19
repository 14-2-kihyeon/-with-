<template>
  <header class="naver-topbar">
    <div class="naver-logo">네이버 뉴스</div>

    <div class="naver-search-area">
      <input
        class="naver-search-input"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        @keyup.enter="$emit('search')"
        placeholder="검색어를 입력하세요. (예: 인공지능, 금융, SSAFY)"
      />
      <button class="naver-search-btn" @click="$emit('search')">검색</button>
    </div>

    <div class="naver-top-buttons">
      <button
        class="naver-top-btn"
        :class="{ active: mode === 'all' }"
        @click="$emit('mode-change', 'all')"
      >
        전체
      </button>
      <button
        class="naver-top-btn"
        :class="{ active: mode === 'bookmark' }"
        @click="$emit('mode-change', 'bookmark')"
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
})
defineEmits(["update:modelValue", "search", "mode-change"])
</script>
