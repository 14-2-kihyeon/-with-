<!-- src/components/main/FeatureSection.vue -->
<template>
  <section
    ref="sectionEl"
    class="home-feature"
    :class="[{ 'is-reverse': reverse, 'is-visible': visible }]"
  >
    <div class="home-feature__inner">
      <!-- 왼쪽(또는 오른쪽) 소개글 -->
      <div class="home-feature__text">
        <h2 class="home-feature__title">{{ title }}</h2>
        <p class="home-feature__desc">{{ description }}</p>

        <div class="home-feature__actions">
          <button class="home-feature__btn" @click="goTo">
            기능 바로가기 →
          </button>
        </div>
      </div>

      <!-- 오른쪽(또는 왼쪽) 캐러셀 -->
      <div class="home-feature__preview">
        <ScreenshotCarousel :images="images" :alt="title" :interval-ms="intervalMs" />
      </div>
    </div>
  </section>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import ScreenshotCarousel from "@/components/main/ScreenshotCarousel.vue"

const props = defineProps({
  title: String,
  description: String,
  images: { type: Array, default: () => [] },
  reverse: { type: Boolean, default: false },
  routeName: { type: String, default: "main" },
  intervalMs: { type: Number, default: 2500 },
})

const router = useRouter()
const sectionEl = ref(null)
const visible = ref(false)

let io = null

const goTo = () => {
  router.push({ name: props.routeName })
}

onMounted(() => {
  io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) visible.value = true
      }
    },
    { threshold: 0.25 }
  )
  if (sectionEl.value) io.observe(sectionEl.value)
})

onBeforeUnmount(() => {
  if (io && sectionEl.value) io.unobserve(sectionEl.value)
  if (io) io.disconnect()
})
</script>

<style scoped>
.home-feature {
  min-height: 100vh;
  display: grid;
  align-items: center;
  scroll-snap-align: start;
  padding: 72px 18px;
}

.home-feature__inner {
  max-width: 1100px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1.05fr 1.25fr;
  gap: 28px;
  align-items: center;
}

/* 좌/우 교차 */
.home-feature.is-reverse .home-feature__text {
  order: 2;
}
.home-feature.is-reverse .home-feature__preview {
  order: 1;
}

/* 등장 애니메이션 */
.home-feature__text,
.home-feature__preview {
  opacity: 0;
  transform: translateY(16px);
  transition: opacity 500ms ease, transform 500ms ease;
}
.home-feature.is-visible .home-feature__text,
.home-feature.is-visible .home-feature__preview {
  opacity: 1;
  transform: translateY(0);
}

.home-feature__title {
  font-size: 34px;
  line-height: 1.15;
  margin: 0 0 12px;
}
.home-feature__desc {
  margin: 0 0 18px;
  font-size: 16px;
  line-height: 1.7;
  opacity: 0.88;
}

.home-feature__actions {
  display: flex;
  gap: 10px;
}
.home-feature__btn {
  border: 1px solid rgba(255,255,255,0.18);
  background: rgba(255,255,255,0.08);
  padding: 10px 14px;
  border-radius: 12px;
  cursor: pointer;
}

/* 반응형: 모바일에서는 세로로 */
@media (max-width: 900px) {
  .home-feature__inner {
    grid-template-columns: 1fr;
  }
  .home-feature.is-reverse .home-feature__text,
  .home-feature.is-reverse .home-feature__preview {
    order: initial;
  }
}
</style>
