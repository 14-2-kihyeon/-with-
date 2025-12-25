<!-- src/components/common/ScrollToTop.vue -->
<template>
  <Transition name="scroll-to-top">
    <button
      v-if="isVisible"
      class="scroll-to-top-btn"
      @click="scrollToTop"
      aria-label="맨 위로 가기"
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 20 20"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M10 16V4M10 4L4 10M10 4L16 10"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
      <span class="btn-text">TOP</span>
    </button>
  </Transition>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from "vue"

const isVisible = ref(false)

const checkScroll = () => {
  // 300px 이상 스크롤하면 버튼 표시
  isVisible.value = window.scrollY > 300
}

const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: "smooth"
  })
}

onMounted(() => {
  window.addEventListener("scroll", checkScroll)
  checkScroll()
})

onBeforeUnmount(() => {
  window.removeEventListener("scroll", checkScroll)
})
</script>

<style scoped>
.scroll-to-top-btn {
  position: fixed;
  right: 32px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;

  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;

  padding: 12px 10px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;

  color: #0f172a;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: -0.01em;

  cursor: pointer;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.scroll-to-top-btn:hover {
  background: #ffffff;
  border-color: rgba(59, 130, 246, 0.3);
  color: #3b82f6;
  transform: translateY(-50%) translateY(-4px);
  box-shadow: 0 8px 30px rgba(59, 130, 246, 0.15);
}

.scroll-to-top-btn:active {
  transform: translateY(-50%) scale(0.95);
}

.scroll-to-top-btn svg {
  width: 20px;
  height: 20px;
  transition: transform 0.3s ease;
}

.scroll-to-top-btn:hover svg {
  transform: translateY(-2px);
}

.btn-text {
  line-height: 1;
}

/* 트랜지션 애니메이션 */
.scroll-to-top-enter-active,
.scroll-to-top-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.scroll-to-top-enter-from {
  opacity: 0;
  transform: translateY(-50%) translateX(20px);
}

.scroll-to-top-leave-to {
  opacity: 0;
  transform: translateY(-50%) translateX(20px);
}

/* 반응형 */
@media (max-width: 768px) {
  .scroll-to-top-btn {
    right: 20px;
    padding: 10px 8px;
  }

  .scroll-to-top-btn svg {
    width: 18px;
    height: 18px;
  }

  .btn-text {
    font-size: 10px;
  }
}

@media (max-width: 480px) {
  .scroll-to-top-btn {
    right: 16px;
    bottom: 24px;
    top: auto;
    transform: none;
  }

  .scroll-to-top-enter-from,
  .scroll-to-top-leave-to {
    transform: translateY(20px);
  }

  .scroll-to-top-btn:hover {
    transform: translateY(-4px);
  }

  .scroll-to-top-btn:active {
    transform: scale(0.95);
  }
}
</style>