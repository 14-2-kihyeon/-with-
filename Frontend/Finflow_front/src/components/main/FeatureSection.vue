<!-- src/components/main/FeatureSection.vue -->
<template>
  <section
    ref="sectionEl"
    class="feature-section"
    :class="[{ 'is-reverse': reverse, 'is-visible': visible, 'is-dark': dark }]"
  >
    <!-- 배경 그라디언트 요소 -->
    <div class="bg-gradient-orb"></div>

    <div class="feature-container">
      <!-- 텍스트 영역 -->
      <div class="feature-content">
        <div class="content-inner">
          <div class="feature-badge">
            <span class="badge-text">{{ title }}</span>
            <div class="badge-shine"></div>
          </div>

          <h2 class="feature-title">
            <span v-for="(word, idx) in descriptionWords" :key="idx" class="title-word" :style="{ transitionDelay: `${idx * 0.25}s` }">
              {{ word }}&nbsp;
            </span>
          </h2>

          <div class="feature-actions">
            <button class="btn-experience" @click="goTo">
              <span class="btn-text">체험하기</span>
              <svg class="btn-arrow" width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M7 3L14 10L7 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <div class="btn-glow"></div>
            </button>
          </div>
        </div>
      </div>

      <!-- 이미지 프리뷰 영역 -->
      <div class="feature-preview">
        <div class="preview-wrapper">
          <div class="preview-glow"></div>
          <ScreenshotCarousel
            :images="images"
            :alt="title"
            :interval-ms="intervalMs"
          />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import ScreenshotCarousel from "@/components/main/ScreenshotCarousel.vue"
import { useChatbot } from "@/composables/useChatbot"

const props = defineProps({
  title: { type: String, default: "" },
  description: { type: String, default: "" },
  images: { type: Array, default: () => [] },
  reverse: { type: Boolean, default: false },
  dark: { type: Boolean, default: false }, // 다크 모드 옵션
  routeName: { type: String, default: "main" },
  intervalMs: { type: Number, default: 2600 },
})

const router = useRouter()
const sectionEl = ref(null)
const visible = ref(false)
const { requestOpenChatbot } = useChatbot()

let io = null

// 단어별로 분리하여 각각 애니메이션 적용
const descriptionWords = computed(() => {
  return props.description.split('\n')
})

const goTo = () => {
  // 챗봇인 경우 플로팅 챗봇 열기
  if (props.routeName === 'chatbot_list') {
    requestOpenChatbot()
  } else {
    router.push({ name: props.routeName })
  }
}

onMounted(() => {
  io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) visible.value = true
      }
    },
    { threshold: 0.65 }
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
   font.css 전역 설정 무시
   Section Base
========================= */
.feature-section {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding: 100px 40px;
  background: #ffffff;
  overflow: hidden;
  transition: background-color 0.6s ease;
}

/* 배경 그라디언트 요소 */
.bg-gradient-orb {
  position: absolute;
  width: 800px;
  height: 800px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, rgba(59, 130, 246, 0) 70%);
  filter: blur(80px);
  pointer-events: none;
  top: 50%;
  left: 20%;
  transform: translate(-50%, -50%);
  opacity: 0;
  transition: opacity 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.4s;
}

.feature-section.is-visible .bg-gradient-orb {
  opacity: 1;
}

/* 짝수 섹션 배경색 교차 */
.feature-section.is-reverse {
  background: #f9fafb;
}

.feature-section.is-reverse .bg-gradient-orb {
  left: 80%;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.12) 0%, rgba(59, 130, 246, 0) 70%);
}

/* 다크 모드 */
.feature-section.is-dark {
  background: #121417;
}

.feature-section.is-dark .bg-gradient-orb {
  background: radial-gradient(circle, rgba(96, 165, 250, 0.25) 0%, rgba(96, 165, 250, 0) 70%);
}

.feature-section.is-dark .feature-badge {
  color: #60a5fa;
}

.feature-section.is-dark .feature-title {
  color: #ffffff;
}

.feature-section.is-dark .btn-experience {
  background: #ffffff;
  color: #121417;
  box-shadow: 0 8px 20px rgba(255, 255, 255, 0.15);
}

.feature-section.is-dark .btn-experience:hover {
  background: #f1f5f9;
  box-shadow: 0 12px 28px rgba(255, 255, 255, 0.25);
}

.feature-section.is-dark .btn-experience .btn-arrow {
  color: #121417;
}

.feature-section.is-dark .preview-wrapper {
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.feature-section.is-dark .preview-wrapper:hover {
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.6);
}

/* 컨테이너 */
.feature-container {
  position: relative;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 100px;
  align-items: center;
}

/* Reverse 레이아웃 */
.feature-section.is-reverse .feature-container {
  grid-template-columns: 1fr 1fr;
}

.feature-section.is-reverse .feature-content {
  order: 2;
}

.feature-section.is-reverse .feature-preview {
  order: 1;
}

/* =========================
   Content (Text Area)
========================= */
.feature-content {
  max-width: 560px;
}

.content-inner {
  max-width: 560px;
}

/* Badge */
.feature-badge {
  position: relative;
  display: inline-block;
  padding: 10px 20px;
  font-size: 17px;
  font-weight: 700;
  color: #3b82f6;
  margin-bottom: 24px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%);
  border: 1.5px solid rgba(59, 130, 246, 0.3);
  border-radius: 20px;
  opacity: 0;
  transform: translateY(80px) scale(0.9);
  transition: all 1s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
}

.badge-text {
  position: relative;
  z-index: 2;
}

.badge-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  animation: shine 3s infinite;
}

@keyframes shine {
  0%, 100% { left: -100%; }
  50% { left: 100%; }
}

.feature-section.is-visible .feature-badge {
  opacity: 1;
  transform: translateY(0) scale(1);
}

/* Title */
.feature-title {
  font-size: clamp(32px, 4.5vw, 64px);
  font-weight: 700;
  line-height: 1.2;
  margin: 0 0 48px 0;
  color: #0f172a;
  letter-spacing: -0.04em !important;
  word-break: keep-all;
}

.title-word {
  display: inline-block;
  font-weight: 700;
  letter-spacing: -0.04em !important;
  -webkit-text-stroke: 0.6px rgba(15, 23, 42, 0.3);
  paint-order: stroke fill;
  opacity: 0;
  transform: translateY(100px) rotateX(90deg);
  transform-origin: bottom center;
  transition: all 1s cubic-bezier(0.16, 1, 0.3, 1);
}

.feature-section.is-visible .title-word {
  opacity: 1;
  transform: translateY(0) rotateX(0deg);
}

/* Actions */
.feature-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  opacity: 0;
  transform: translateY(60px);
  transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.2s;
}

.feature-section.is-visible .feature-actions {
  opacity: 1;
  transform: translateY(0);
}

/* Experience Button */
.btn-experience {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px 44px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  border-radius: 50px;
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3), 0 4px 12px rgba(59, 130, 246, 0.2);
}

.btn-text {
  position: relative;
  z-index: 2;
  transition: transform 0.3s ease;
}

.btn-arrow {
  position: relative;
  z-index: 2;
  transition: transform 0.3s ease;
  opacity: 0.9;
}

.btn-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width 0.6s ease, height 0.6s ease;
}

.btn-experience:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 16px 40px rgba(59, 130, 246, 0.4), 0 8px 16px rgba(59, 130, 246, 0.3);
}

.btn-experience:hover .btn-text {
  transform: translateX(-2px);
}

.btn-experience:hover .btn-arrow {
  transform: translateX(4px);
  opacity: 1;
}

.btn-experience:hover .btn-glow {
  width: 300px;
  height: 300px;
}

.btn-experience:active {
  transform: translateY(-2px) scale(0.98);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
}

/* =========================
   Preview (Image Area)
========================= */
.feature-preview {
  position: relative;
  opacity: 0;
  transform: translateY(80px) scale(0.95);
  transition: all 1s cubic-bezier(0.16, 1, 0.3, 1) 0.3s;
}

.feature-section.is-visible .feature-preview {
  opacity: 1;
  transform: translateY(0) scale(1);
}

/* Preview Wrapper */
.preview-wrapper {
  position: relative;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 25px 70px rgba(15, 23, 42, 0.15), 0 10px 30px rgba(15, 23, 42, 0.1);
  transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: transform;
}

.preview-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.3) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.6s ease;
  pointer-events: none;
  z-index: 1;
}

.preview-wrapper:hover {
  transform: translateY(-12px) scale(1.02) rotateX(2deg);
  box-shadow: 0 35px 90px rgba(15, 23, 42, 0.2), 0 15px 40px rgba(59, 130, 246, 0.15);
}

.preview-wrapper:hover .preview-glow {
  opacity: 1;
}

.preview-wrapper:active {
  transform: translateY(-8px) scale(1.01);
}

/* =========================
   Responsive Design
========================= */
@media (max-width: 1280px) {
  .feature-container {
    gap: 80px;
  }

  .feature-section {
    padding: 80px 32px;
  }
}

@media (max-width: 1024px) {
  .feature-container {
    gap: 60px;
  }

  .feature-title {
    font-size: clamp(32px, 4vw, 48px);
    margin-bottom: 36px;
  }
}

@media (max-width: 768px) {
  .feature-section {
    min-height: auto;
    padding: 60px 24px;
  }

  .feature-container {
    grid-template-columns: 1fr;
    gap: 48px;
  }

  .feature-section.is-reverse .feature-container {
    grid-template-columns: 1fr;
  }

  .feature-content {
    order: 1;
    text-align: center;
  }

  .feature-section.is-reverse .feature-content {
    order: 1;
  }

  .feature-preview {
    order: 2;
  }

  .feature-section.is-reverse .feature-preview {
    order: 2;
  }

  .content-inner {
    max-width: 100%;
  }

  .feature-badge {
    margin: 0 auto 16px;
  }

  .feature-title {
    margin-bottom: 32px;
  }

  .feature-actions {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .feature-section {
    padding: 48px 20px;
  }

  .feature-title {
    font-size: 32px;
    margin-bottom: 28px;
  }

  .btn-experience {
    width: 100%;
    padding: 16px 32px;
  }
}
</style>