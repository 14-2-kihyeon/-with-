<!-- src/components/main/ScreenshotCarousel.vue -->
<template>
  <div class="home-carousel">
    <Transition name="home-slide" mode="out-in">
      <img
        v-if="activeSrc"
        :key="activeSrc"
        class="home-carousel__img"
        :src="activeSrc"
        :alt="alt"
        loading="lazy"
      />
    </Transition>
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
let timer = null

const activeSrc = computed(() => {
  if (!props.images?.length) return ""
  return props.images[idx.value]
})

onMounted(() => {
  if (!props.images?.length) return
  timer = setInterval(() => {
    idx.value = (idx.value + 1) % props.images.length
  }, props.intervalMs)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
/* ✅ 박스 크기 일정(중요) */
.home-carousel {
  width: 100%;
  height: clamp(220px, 40vh, 420px); /* ✅ 항상 일정한 “체감 크기” */
  border-radius: 18px;
  overflow: hidden;

  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);

  display: flex;
  align-items: center;
  justify-content: center;

  padding: 14px;
  box-sizing: border-box;
}

.home-carousel__img {
  width: 100%;
  height: 100%;
  object-fit: contain;  /* ✅ 안 잘림 */
}

/* ✅ 이전은 왼쪽으로 나가고, 다음은 오른쪽에서 중앙으로 */
.home-slide-enter-from {
  transform: translateX(55%);
  opacity: 0;
}
.home-slide-enter-to {
  transform: translateX(0);
  opacity: 1;
}
.home-slide-enter-active {
  transition: transform 450ms ease, opacity 450ms ease;
}

.home-slide-leave-from {
  transform: translateX(0);
  opacity: 1;
}
.home-slide-leave-to {
  transform: translateX(-55%);
  opacity: 0;
}
.home-slide-leave-active {
  transition: transform 450ms ease, opacity 450ms ease;
}
</style>
