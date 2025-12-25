<template>
  <div class="layout">
    <NavBar />

    <!-- 고정 배경 레이어 -->
    <div class="bg" aria-hidden="true"></div>

    <!-- 히어로 섹션 -->
    <HeroSection v-if="isMain" :next-el-id="NEXT_SECTION_ID" :nav-height="NAV_HEIGHT" />

    <PopUp v-if="isMain" v-model="showPromo" :storage-key="PROMO_STORAGE_KEY" :image-src="promoImage" image-alt="투자 성향 분석 프로모션" @survey="onSurvey" />

    <!-- 실제 콘텐츠 레이어 -->
    <main class="content" :class="{ 'content--main': isMain }">
      <div class="content-inner" :id="isMain ? NEXT_SECTION_ID : undefined">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import NavBar from "@/components/common/NavBar.vue"
import HeroSection from "@/components/main/HeroSection.vue";
import PopUp from "@/components/common/PopUp.vue";
import popupImage from "@/assets/main/popup3.png" 

const promoImage = popupImage


const route = useRoute()
const router = useRouter()
const NAV_HEIGHT = 84
const NEXT_SECTION_ID = "main-content-start"

const isMain = computed(() => route.name === "main")

const showPromo = ref(false)
let promoTimer = null

const PROMO_STORAGE_KEY = "pb_promo_hide_until"

const todayKey = () => {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  return `${y}-${m}-${day}`
}

const isHiddenToday = () => {
  try {
    return localStorage.getItem(PROMO_STORAGE_KEY) === todayKey()
  } catch {
    return false
  }
}

const clearPromoTimer = () => {
  if (promoTimer) window.clearTimeout(promoTimer)
  promoTimer = null
}

const schedulePromo = () => {
  clearPromoTimer()

  if (!isMain.value) return
  if (isHiddenToday()) return

  // 기존 타이머 제거 후 재설정
  if (promoTimer) window.clearTimeout(promoTimer)

  promoTimer = window.setTimeout(() => {
    // 메인에 있을 때만 표시
    if (isMain.value) showPromo.value = true
  }, 3240)
}

const onSurvey = () => {
  router.push({ name: "investment_survey" })
}

onMounted(() => {
  schedulePromo()
})

onBeforeUnmount(() => {
  clearPromoTimer()
})

// 메인으로 돌아올 때마다 스케줄 다시 잡기
watch(
  () => route.name,
  () => {
    showPromo.value = false
    clearPromoTimer()
    schedulePromo()
  }
)

</script>

<style scoped>
/* 전체 레이아웃 */
.layout {
  min-height: 100vh;
}

/* 배경: 이미지 + (거의 안 보이게) 연한 회색 오버레이 */
.bg {
  position: fixed;
  inset: 0;
  background-image: url("@/assets/main/main.png");
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-attachment: fixed;
  z-index: -1;
}

/* ✅ 상단은 완전 흰색(네비와 경계 없음) → 아래로 갈수록 살짝 보이게 */
.bg::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom,
      rgba(255, 255, 255, var(--bg-a-top, 0.96)) 0%,
      rgba(245, 245, 245, var(--bg-a-mid, 0.14)) 35%,
      rgba(245, 245, 245, var(--bg-a-bot, 0.08)) 100%);
  pointer-events: none;
  transition: background 140ms linear;
}

/* 콘텐츠 영역: 가로 중앙 정렬 */
.content {
  position: relative;
  z-index: 0;
  min-height: 100vh;
  padding: 16px 16px 0px;

  display: flex;
  justify-content: center;
  /* 가로 가운데 */
  align-items: flex-start;
  /* 세로는 위에서 시작(길어져도 자연스럽게 스크롤) */
}

/* ✅ main 페이지는 Hero가 100vh를 차지하므로, 콘텐츠는 위 여백 불필요 */
.content--main {
  padding-top: 0;
}

/* RouterView 들어올 “카드” */
.content-inner {
  width: min(1400px, 100%);
  background: rgba(255, 255, 255, 0.92);
  /* 배경과 구분 */
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
  padding: clamp(16px, 2.2vw, 28px);
}
</style>
