<!-- src/components/main/ScreenshotCarousel.vue -->
<template>
  <div class="screenshot-carousel">
    <!-- 진행 인디케이터 -->
    <div class="carousel-indicators">
      <div
        v-for="(_, i) in images"
        :key="i"
        class="indicator"
        :class="{ active: i === idx }"
        @click="() => { idx = i; resetProgress(); }"
      >
        <div class="indicator-progress" :style="{ width: i === idx ? progressWidth : '0%' }"></div>
      </div>
    </div>

    <!-- 이미지 슬라이드 -->
    <div class="carousel-content">
      <Transition name="carousel-slide" mode="out-in">
        <div
          v-if="activeSrc"
          :key="activeSrc"
          class="carousel-image-wrapper"
        >
          <img
            class="carousel-image"
            :src="activeSrc"
            :alt="alt"
            loading="lazy"
          />
        </div>
      </Transition>
    </div>

    <!-- 네비게이션 버튼 -->
    <button
      v-if="images.length > 1"
      class="carousel-nav prev"
      @click="prev"
      aria-label="이전 이미지"
    >
      ‹
    </button>
    <button
      v-if="images.length > 1"
      class="carousel-nav next"
      @click="next"
      aria-label="다음 이미지"
    >
      ›
    </button>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue"

const props = defineProps({
  images: { type: Array, required: true },
  intervalMs: { type: Number, default: 2500 },
  alt: { type: String, default: "feature preview" },
})

const idx = ref(0)
const progressWidth = ref('0%')
let timer = null
let progressTimer = null

const activeSrc = computed(() => {
  if (!props.images?.length) return ""
  return props.images[idx.value]
})

const next = () => {
  idx.value = (idx.value + 1) % props.images.length
  resetProgress()
}

const prev = () => {
  idx.value = (idx.value - 1 + props.images.length) % props.images.length
  resetProgress()
}

const resetProgress = () => {
  progressWidth.value = '0%'
  if (progressTimer) clearTimeout(progressTimer)
  progressTimer = setTimeout(() => {
    progressWidth.value = '100%'
  }, 50)
}

onMounted(() => {
  if (!props.images?.length) return

  resetProgress()

  timer = setInterval(() => {
    next()
  }, props.intervalMs)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  if (progressTimer) clearTimeout(progressTimer)
})
</script>

<style scoped>
.screenshot-carousel {
  position: relative;
  width: 100%;
  height: clamp(400px, 50vh, 600px);
  border-radius: 16px;
  overflow: hidden;
  background: #ffffff;
}

/* 진행 인디케이터 */
.carousel-indicators {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 10;
}

.indicator {
  position: relative;
  width: 32px;
  height: 3px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 2px;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
}

.indicator:hover {
  background: rgba(255, 255, 255, 0.6);
}

.indicator.active {
  background: rgba(255, 255, 255, 0.5);
}

.indicator-progress {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: #ffffff;
  border-radius: 2px;
  transition: width 2.5s linear;
}

/* 이미지 컨텐츠 */
.carousel-content {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
}

.carousel-image-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.carousel-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

/* 네비게이션 버튼 */
.carousel-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.95);
  border: none;
  font-size: 20px;
  color: #0f172a;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  z-index: 10;
  opacity: 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.screenshot-carousel:hover .carousel-nav {
  opacity: 1;
}

.carousel-nav:hover {
  background: #ffffff;
  transform: translateY(-50%) scale(1.05);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.carousel-nav:active {
  transform: translateY(-50%) scale(0.98);
}

.carousel-nav.prev {
  left: 20px;
}

.carousel-nav.next {
  right: 20px;
}

/* 슬라이드 애니메이션 */
.carousel-slide-enter-from {
  transform: scale(0.98);
  opacity: 0;
}

.carousel-slide-enter-to {
  transform: scale(1);
  opacity: 1;
}

.carousel-slide-enter-active {
  transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.carousel-slide-leave-from {
  transform: scale(1);
  opacity: 1;
}

.carousel-slide-leave-to {
  transform: scale(0.98);
  opacity: 0;
}

.carousel-slide-leave-active {
  transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

/* 반응형 */
@media (max-width: 768px) {
  .screenshot-carousel {
    height: clamp(280px, 40vh, 420px);
  }

  .carousel-nav {
    width: 36px;
    height: 36px;
    font-size: 18px;
  }

  .carousel-nav.prev {
    left: 16px;
  }

  .carousel-nav.next {
    right: 16px;
  }

  .indicator {
    width: 28px;
  }

  .carousel-indicators {
    bottom: 20px;
  }
}
</style>
