<template>
  <div class="layout">
    <NavBar />

    <!-- 고정 배경 레이어 -->
    <div class="bg" aria-hidden="true"></div>

    <!-- 실제 콘텐츠 레이어 -->
    <main class="content">
      <div class="content-inner">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<script setup>
import NavBar from "@/components/common/NavBar.vue"
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
  background-image: url("@/assets/main/kakaomap/Background.png");
  opacity: 0.3; /* 투명도 조절 */
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-attachment: fixed;
  z-index: -1;
}

/* 연한 회색 오버레이(배경이 거의 안 보이게) */
.bg::after {
  content: "";
  position: absolute;
  inset: 0;
  background: rgba(245, 245, 245, 0.95); /* 0.95면 배경 거의 안 보임 */
  pointer-events: none;
}

/* 콘텐츠 영역: 가로 중앙 정렬 */
.content {
  position: relative;
  z-index: 0;
  min-height: 100vh;
  padding: 24px 16px 48px;

  display: flex;
  justify-content: center;   /* 가로 가운데 */
  align-items: flex-start;   /* 세로는 위에서 시작(길어져도 자연스럽게 스크롤) */
}

/* RouterView 들어올 “카드” */
.content-inner {
  width: min(1100px, 100%);
  background: rgba(255, 255, 255, 0.92); /* 배경과 구분 */
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
  padding: clamp(16px, 2.2vw, 28px);
}
</style>
