<!-- src/components/common/ResultVideoPopup.vue -->
<template>
  <transition name="fade">
    <div v-if="isVisible" class="video-popup-overlay" @click="handleOverlayClick">
      <div class="video-popup-container" @click.stop>
        <!-- 닫기 버튼 -->
        <button class="close-btn" @click="closePopup">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>

        <!-- 동영상 플레이어 -->
        <div class="video-wrapper">
          <video
            ref="videoPlayer"
            :src="videoSrc"
            @ended="onVideoEnded"
            autoplay
            controls
            class="result-video"
          >
            <p>브라우저가 비디오 재생을 지원하지 않습니다.</p>
          </video>

          <!-- 동영상 종료 후 투자 성향 텍스트 -->
          <transition name="fade-scale">
            <div v-if="showEndText" class="investment-type-overlay">
              <div class="investment-type-text">
                {{ investmentTypeText }}
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'

// 동영상 파일 명시적 import
import timidMaleVideo from '@/assets/video/timid_male.mp4'
import timidFemaleVideo from '@/assets/video/timid_female.mp4'
import normalMaleVideo from '@/assets/video/normal_male.mp4'
import normalFemaleVideo from '@/assets/video/normal_female.mp4'
import speculativeMaleVideo from '@/assets/video/speculative_male.mp4'
import speculativeFemaleVideo from '@/assets/video/speculative_female.mp4'

const props = defineProps({
  riskType: {
    type: String,
    required: true
  },
  show: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const isVisible = ref(false)
const videoPlayer = ref(null)
const showEndText = ref(false)

// risk_type에 따른 동영상 경로 매핑
const videoSrc = computed(() => {
  if (!props.riskType) {
    console.warn('riskType이 없습니다.')
    return ''
  }

  const videoMap = {
    timid_male: timidMaleVideo,
    timid_female: timidFemaleVideo,
    normal_male: normalMaleVideo,
    normal_female: normalFemaleVideo,
    speculative_male: speculativeMaleVideo,
    speculative_female: speculativeFemaleVideo,
  }

  const video = videoMap[props.riskType]

  if (!video) {
    console.error(`동영상을 찾을 수 없습니다: ${props.riskType}`)
    return ''
  }

  console.log('동영상 경로:', video)
  return video
})

// risk_type에 따른 투자 성향 텍스트 매핑
const investmentTypeText = computed(() => {
  const textMap = {
    speculative_male: '테토 투기남',
    speculative_female: '테토 투기녀',
    normal_male: '보통남',
    normal_female: '보통녀',
    timid_male: '에겐 소심남',
    timid_female: '에겐 소심녀',
  }
  return textMap[props.riskType] || '투자자'
})

// 팝업 표시 상태 감시
watch(() => props.show, async (newVal) => {
  console.log('팝업 상태 변경:', newVal, 'riskType:', props.riskType)
  isVisible.value = newVal

  if (newVal) {
    // 팝업이 열릴 때 body 스크롤 방지
    document.body.style.overflow = 'hidden'

    // DOM 렌더링 완료 후 비디오 자동 재생
    await nextTick()

    if (videoPlayer.value) {
      console.log('비디오 재생 시작:', videoSrc.value)
      videoPlayer.value.play().catch(err => {
        console.error('비디오 자동 재생 실패:', err)
      })
    } else {
      console.error('videoPlayer ref가 없습니다.')
    }
  } else {
    // 팝업이 닫힐 때 body 스크롤 복구
    document.body.style.overflow = ''
  }
}, { immediate: true })

const closePopup = () => {
  // 비디오 정지
  if (videoPlayer.value) {
    videoPlayer.value.pause()
    videoPlayer.value.currentTime = 0
  }

  // 상태 초기화
  showEndText.value = false
  isVisible.value = false
  emit('close')
}

const handleOverlayClick = () => {
  // 오버레이 클릭 시 팝업 닫기
  closePopup()
}

const onVideoEnded = () => {
  // 동영상이 끝나면 투자 성향 텍스트 표시
  console.log('동영상 재생 완료')
  showEndText.value = true
}

// ESC 키로 팝업 닫기
const handleEscKey = (e) => {
  if (e.key === 'Escape' && isVisible.value) {
    closePopup()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscKey)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleEscKey)
  // 컴포넌트 언마운트 시 스크롤 복구
  document.body.style.overflow = ''
})
</script>

<style scoped>
/* 오버레이 */
.video-popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

/* 팝업 컨테이너 */
.video-popup-container {
  position: relative;
  width: 100%;
  max-width: 900px;
  background: #1a1a1a;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 25px 70px rgba(0, 0, 0, 0.4);
  animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(40px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 닫기 버튼 */
.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
  transition: all 0.3s ease;
  z-index: 10;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: rotate(90deg);
}

.close-btn:active {
  transform: rotate(90deg) scale(0.95);
}

/* 비디오 래퍼 */
.video-wrapper {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 비율 */
  background: #000;
}

.result-video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  outline: none;
}

/* 투자 성향 텍스트 오버레이 */
.investment-type-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 5;
  pointer-events: none;
}

.investment-type-text {
  padding: 32px 64px;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(12px);
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 24px;
  font-size: 48px;
  font-weight: 800;
  color: #ffffff;
  text-align: center;
  letter-spacing: 0.05em;
  text-shadow:
    0 0 20px rgba(59, 130, 246, 0.8),
    0 0 40px rgba(59, 130, 246, 0.5),
    0 4px 12px rgba(0, 0, 0, 0.8);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.5),
    0 0 40px rgba(59, 130, 246, 0.3),
    inset 0 0 20px rgba(59, 130, 246, 0.1);
  animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
  from {
    box-shadow:
      0 20px 60px rgba(0, 0, 0, 0.5),
      0 0 40px rgba(59, 130, 246, 0.3),
      inset 0 0 20px rgba(59, 130, 246, 0.1);
  }
  to {
    box-shadow:
      0 20px 60px rgba(0, 0, 0, 0.5),
      0 0 60px rgba(59, 130, 246, 0.6),
      inset 0 0 30px rgba(59, 130, 246, 0.2);
  }
}

/* 페이드 스케일 트랜지션 */
.fade-scale-enter-active {
  animation: fadeScaleIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

.fade-scale-leave-active {
  animation: fadeScaleOut 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fadeScaleIn {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.5);
  }
  50% {
    transform: translate(-50%, -50%) scale(1.1);
  }
  100% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

@keyframes fadeScaleOut {
  from {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
  to {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.8);
  }
}

/* 페이드 트랜지션 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 반응형 */
@media (max-width: 768px) {
  .video-popup-overlay {
    padding: 16px;
  }

  .video-popup-container {
    max-width: 100%;
    border-radius: 16px;
  }

  .close-btn {
    width: 40px;
    height: 40px;
    top: 12px;
    right: 12px;
  }

  .investment-type-text {
    padding: 24px 48px;
    font-size: 36px;
    border-width: 2px;
  }
}

@media (max-width: 480px) {
  .video-popup-overlay {
    padding: 0;
  }

  .video-popup-container {
    border-radius: 0;
    max-width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .video-wrapper {
    padding-top: 0;
    height: auto;
    flex: 1;
    display: flex;
    align-items: center;
  }

  .result-video {
    position: relative;
  }

  .investment-type-text {
    padding: 20px 32px;
    font-size: 28px;
    border-width: 2px;
    border-radius: 16px;
    white-space: nowrap;
  }
}
</style>
