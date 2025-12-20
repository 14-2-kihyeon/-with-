<template>
  <div class="layout">
    <NavBar />

    <!-- 고정 배경 레이어 -->
    <div class="bg" aria-hidden="true"></div>

    <!-- 히어로 섹션 -->
    <HeroSection
      v-if="isMain"
      :next-el-id="NEXT_SECTION_ID"
      :nav-height="NAV_HEIGHT"
    />

    <!-- 실제 콘텐츠 레이어 -->
    <main class="content" :class="{ 'content--main': isMain }">
      <div
        class="content-inner"
        :id="isMain ? NEXT_SECTION_ID : undefined"
      >
        <RouterView />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import { useRoute } from "vue-router"
import NavBar from "@/components/common/NavBar.vue"
import HeroSection from "@/components/main/HeroSection.vue";

const route = useRoute()

const NAV_HEIGHT = 84
const NEXT_SECTION_ID = "main-content-start"

const isMain = computed(() => route.name === "main")

/** ✅ 스크롤에 따라 NavBar 스타일 변경 */
const navScrolled = ref(false)

const onScroll = () => {
  // Hero 구간에서는 "투명 느낌", 조금만 내려가면 solid+shadow
  navScrolled.value = window.scrollY > 12
}

onMounted(() => {
  window.addEventListener("scroll", onScroll, { passive: true })
  onScroll()
})

onBeforeUnmount(() => {
  window.removeEventListener("scroll", onScroll)
})
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
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.98) 0%,
    rgba(245, 245, 245, 0.70) 35%,
    rgba(245, 245, 245, 0.55) 100%
  );
  pointer-events: none;
}

/* 콘텐츠 영역: 가로 중앙 정렬 */
.content {
  position: relative;
  z-index: 0;
  min-height: 100vh;
  padding: 16px 16px 0px;

  display: flex;
  justify-content: center;   /* 가로 가운데 */
  align-items: flex-start;   /* 세로는 위에서 시작(길어져도 자연스럽게 스크롤) */
}

/* ✅ main 페이지는 Hero가 100vh를 차지하므로, 콘텐츠는 위 여백 불필요 */
.content--main {
  padding-top: 0;
}

/* RouterView 들어올 “카드” */
.content-inner {
  width: min(1400px, 100%);
  background: rgba(255, 255, 255, 0.92); /* 배경과 구분 */
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
  padding: clamp(16px, 2.2vw, 28px);
}
</style>
