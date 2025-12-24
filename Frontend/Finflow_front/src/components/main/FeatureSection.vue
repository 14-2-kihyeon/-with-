<!-- src/components/main/FeatureSection.vue -->
<template>
  <section
    ref="sectionEl"
    class="home-feature"
    :class="[{ 'is-reverse': reverse, 'is-visible': visible }]"
  >
    <div class="home-feature__inner">
      <!-- 텍스트 -->
      <div class="home-feature__text">
        <h2 class="home-feature__title">{{ title }}</h2>
        <p class="home-feature__desc">{{ description }}</p>

        <div class="home-feature__actions">
          <button class="home-feature__btn" @click="goTo">
            바로가기 →
          </button>
        </div>
      </div>

      <!-- 이미지(캐러셀) -->
      <div class="home-feature__preview">
        <ScreenshotCarousel
          :images="images"
          :alt="title"
          :interval-ms="intervalMs"
        />
      </div>
    </div>
  </section>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import ScreenshotCarousel from "@/components/main/ScreenshotCarousel.vue"

const props = defineProps({
  title: { type: String, default: "" },
  description: { type: String, default: "" },
  images: { type: Array, default: () => [] },
  reverse: { type: Boolean, default: false },
  routeName: { type: String, default: "main" },
  intervalMs: { type: Number, default: 2600 },
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
    { threshold: 0.2 }
  )
  if (sectionEl.value) io.observe(sectionEl.value)
})

onBeforeUnmount(() => {
  if (io && sectionEl.value) io.unobserve(sectionEl.value)
  if (io) io.disconnect()
})
</script>

<style scoped>
/* =========================
   Section base
========================= */
.home-feature {
  min-height: clamp(520px, 78vh, 820px);
  display: flex;
  align-items: center;
  padding: 28px 18px;
  scroll-snap-align: start;
  box-sizing: border-box;
}

.home-feature__inner {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;

  display: grid;
  grid-template-columns: 1fr 1.35fr; /* 텍스트(좁게) + 이미지(넓게) */
  gap: 26px;
  align-items: center;
}

/* reverse(이미지 왼쪽, 텍스트 오른쪽) */
.home-feature.is-reverse .home-feature__inner {
  grid-template-columns: 1.35fr 1fr;
}

.home-feature.is-reverse .home-feature__text {
  order: 2;
}
.home-feature.is-reverse .home-feature__preview {
  order: 1;
}

/* =========================
   Text styles
========================= */
.home-feature__title {
  font-size: 34px;
  line-height: 1.15;
  margin: 0 0 10px;
}

.home-feature__desc {
  margin: 0 0 14px;
  font-size: 16px;
  line-height: 1.7;
  opacity: 0.88;
}

.home-feature__actions {
  display: flex;
  gap: 10px;
}

.home-feature__btn {
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.08);
  padding: 10px 14px;
  border-radius: 12px;
  cursor: pointer;
}

.home-feature__preview {
  justify-self: center;
  width: min(720px, 100%);
}

/* =========================
   Appear animation
========================= */
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

/* =========================
   ✅ Mobile: ALWAYS stack
   (reverse 섹션도 무조건 아래로 내려가게!)
========================= */
@media (max-width: 980px) {
  .home-feature {
    min-height: auto;
    padding: 22px 16px;
  }

  /* 기본 섹션 1열 */
  .home-feature__inner {
    grid-template-columns: 1fr;
    gap: 14px;
    justify-items: center;
  }

  /* ✅ 핵심: reverse가 이기는 문제를 reverse 선택자로 다시 덮어쓰기 */
  .home-feature.is-reverse .home-feature__inner {
    grid-template-columns: 1fr;
  }

  /* 텍스트 가운데 + 버튼 가운데 */
  .home-feature__text {
    order: 1;
    text-align: center;
  }
  .home-feature__actions {
    justify-content: center;
  }

  /* 이미지 아래로 */
  .home-feature__preview {
    order: 2;
    width: min(720px, 100%);
  }

  /* ✅ reverse 섹션도 강제로 동일하게 */
  .home-feature.is-reverse .home-feature__text {
    order: 1;
    text-align: center;
  }
  .home-feature.is-reverse .home-feature__preview {
    order: 2;
  }
}
</style>
