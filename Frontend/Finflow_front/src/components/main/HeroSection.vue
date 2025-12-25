<template>
    <section class="hero" :style="{ '--nav-h': navHeight + 'px' }">
        <div class="hero-inner" :class="{ 'is-in': mounted }">
            <h1 class="hero-title">
              <br>
                <span class="hero-line line-1">투자의 모든 것</span><br />

                <span class="hero-line line-2">
                    <img class="hero-logo" src="@/assets/navbar/logo.png" alt="Personal Bank" />
                    와 스마트하게
                </span>
            </h1>

            <p class="hero-sub hero-line line-3">
                <strong>투자 성향 기반 예·적금 비교부터 추천, 주식 정보까지 한 곳에서.</strong>
            </p>
        </div>

        <button class="hero-scroll" type="button" @click="scrollToNext" aria-label="Scroll down">
            <!-- 큰 chevron-down 아이콘 -->
            <svg viewBox="0 0 24 24" width="34" height="34" fill="none" aria-hidden="true">
                <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"
                    stroke-linejoin="round" />
            </svg>
        </button>
    </section>
</template>

<script setup>
import { onMounted, ref } from "vue"

const props = defineProps({
    nextElId: { type: String, required: true },
    navHeight: { type: Number, default: 84 }
})

const mounted = ref(false)

onMounted(() => {
    // ✅ 텍스트 페이드 인 트리거
    requestAnimationFrame(() => {
        mounted.value = true
    })
})

const scrollToNext = () => {
    const el = document.getElementById(props.nextElId)
    if (!el) {
        // fallback: 1뷰포트 스크롤
        window.scrollBy({ top: window.innerHeight, behavior: "smooth" })
        return
    }

    // ✅ 네비 높이만큼 보정해서 정확히 '카드 상단'이 보이게
    const top = el.getBoundingClientRect().top + window.scrollY - props.navHeight + 30
    window.scrollTo({ top, behavior: "smooth" })
}
</script>

<style scoped>
/* Hero 자체가 100vh를 정확히 차지하도록 */
.hero {
    height: 94vh;
    position: relative;
    display: grid;
    place-items: center;

    /* ✅ NavBar가 sticky라서 겹치므로 그만큼 위 여백 */
    padding-top: var(--nav-h);
    box-sizing: border-box;

    /* 텍스트가 중앙보다 위로 오게 */
    align-content: start;
}

.hero-logo {
    display: inline-block;
    vertical-align: middle;
    margin-right: 10px;
    margin-bottom: 16px;
    width: 400px;
    height: auto;
    /* 비율 유지 */
    object-fit: contain;
    transform: scale(0.96);
    transition: transform 600ms ease;
}

/* ✅ 기존 margin-top이 너무 큼 → 줄이거나 제거 */
.hero-inner {
    margin-top: 0;
    /* <-- 1순위로 이것부터 적용 */
    transform: translateY(-36px);
    /* <-- 중앙에서 살짝 위로만 끌어올림 */

    text-align: center;
    max-width: 980px;
    padding: 0 20px;
}

.hero-inner.is-in {
    opacity: 1;
    transform: translateY(-36px);
    /* 페이드인 후에도 같은 위치 유지 */
}

/* 가독성: 배경 위에서 선명하게 */
.hero-title {
    margin: 0;
    font-size: clamp(34px, 5.6vw, 64px);
    line-height: 1.18;
    font-weight: 900;
    color: rgba(15, 23, 42, 0.92);
    text-shadow: 0 8px 22px rgba(255, 255, 255, 0.55);
    -webkit-text-stroke: 0.5px rgba(15, 23, 42, 0.3);
    paint-order: stroke fill;
}

.hero-title strong {
    font-weight: 900;
}

.hero-line.line-1,
.hero-line.line-2 {
    font-weight: 700;
    -webkit-text-stroke: 0.8px rgba(15, 23, 42, 0.25);
}

.hero-sub {
    margin: 14px 0 0;
    font-size: clamp(14px, 1.7vw, 18px);
    line-height: 1.6;
    color: rgba(15, 23, 42, 0.72);
    text-shadow: 0 8px 22px rgba(255, 255, 255, 0.55);
}

.hero-line {
  display: inline-flex;
  align-items: center;
  justify-content: center;

  opacity: 0;
  transform: translateY(14px);
  transition:
    opacity 600ms ease,
    transform 600ms ease;
}

/* hero-inner가 is-in 되면 등장 */
.hero-inner.is-in .hero-line {
  opacity: 1;
  transform: translateY(0);
}

/* 줄별 딜레이 */
.hero-inner.is-in .line-1 {
  transition-delay: 180ms;
}

.hero-inner.is-in .line-2 {
  transition-delay: 900ms;
}

.hero-inner.is-in .line-3 {
  transition-delay: 1620ms;
}

/* 등장 시 로고만 살짝 커짐 */
.hero-inner.is-in .line-2 .hero-logo {
  transform: scale(1);
}

/* ✅ 스크롤 버튼: 더 크고 명확하게 */
.hero-scroll {
    position: absolute;
    left: 50%;
    bottom: max(56px, env(safe-area-inset-bottom));
    /* 모바일 하단 안전영역 대응 */
    transform: translateX(-50%);

    width: 56px;
    height: 56px;
    border-radius: 999px;

    border: 1px solid rgba(15, 23, 42, 0.12);
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(10px);

    display: grid;
    place-items: center;
    cursor: pointer;

    color: rgba(15, 23, 42, 0.75);
    box-shadow: 0 14px 30px rgba(15, 23, 42, 0.10);

    animation: float 1.8s ease-in-out infinite;
    transition: transform 160ms ease, background 160ms ease, color 160ms ease;
}

.hero-scroll:hover {
    background: rgba(255, 255, 255, 0.92);
    color: rgba(29, 78, 216, 0.9);
    transform: translateX(-50%) scale(1.03);
}

/* 일정 속도로 위아래 */
@keyframes float {
    0% {
        transform: translate(-50%, 0);
    }

    50% {
        transform: translate(-50%, 10px);
    }

    100% {
        transform: translate(-50%, 0);
    }
}

/* 모바일에서 텍스트가 너무 내려오지 않게 */
@media (max-width: 600px) {
    .hero-inner {
        margin-top: 64px;
    }
}
</style>