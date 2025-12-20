<template>
  <div class="layout">
    <NavBar />

    <!-- 고정 배경 레이어 -->
    <div class="bg" aria-hidden="true"></div>

    <!-- 실제 콘텐츠 레이어 -->
    <main class="content">
      <RouterView />
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

/* 배경: 스크롤해도 고정 + 화면 전체 cover */
.bg {
  position: fixed;
  inset: 0; /* top:0; right:0; bottom:0; left:0; */
  background-image: url("@/assets/main/kakaomap/Background.png");
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-attachment: fixed; /* 일부 브라우저 보강용 */
  z-index: -1; /* 콘텐츠 뒤로 */
}

/* 콘텐츠 영역: 배경 위에 올라오도록 */
.content {
  position: relative;
  z-index: 0;
  min-height: 100vh;
  padding: 16px;
}

/* RouterView 내부 콘텐츠가 잘 보이게 필요 시 반투명 배경을 줄 수 있음
.content :deep(.page) { background: rgba(255,255,255,0.85); border-radius: 12px; padding: 16px; }
*/
</style>