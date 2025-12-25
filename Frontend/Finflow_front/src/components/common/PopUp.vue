<template>
    <Teleport to="body">
        <div v-if="modelValue" class="popup-overlay" role="dialog" aria-modal="true" aria-labelledby="popup-title"
            @click.self="handleClose(false)">
            <!-- 포스터형 팝업 -->
            <div class="popup">
                <!-- 이미지 영역 -->
                <div class="popup-media">
                    <img v-if="imageSrc" class="popup-img" :src="imageSrc" :alt="imageAlt" />

                    <!-- 이미지가 없을 때 fallback(원하면 제거 가능) -->
                    <div v-else class="popup-img-fallback">
                        <div class="fallback-text">PROMO</div>
                    </div>

                    <!-- 그라데이션 오버레이 -->
                    <div class="popup-gradient" />

                    <!-- NEW + 카피 오버레이 -->
                    <div class="popup-copy" aria-hidden="true">
                        <div class="popup-pill">NEW</div>

                        <h3 class="popup-headline">
                            PBTI 검사로 알아보는<br />
                            나의 투자 성향<br />
                        </h3> 

                        <p class="popup-lead">
                            맞춤형 금융 상품 추천도<br />
                            놓치지 마세요.
                        </p>+
                    </div>


                    <!-- 체크박스: 이미지 하단 좌측 -->
                    <label class="popup-check">
                        <input type="checkbox" v-model="dontShowToday" />
                        <span>오늘 하루 보지 않기</span>
                    </label>
                </div>

                <!-- 하단 버튼 바(70px 고정) -->
                <div class="popup-actions">
                    <button class="popup-btn primary" type="button" @click="goSurvey">
                        내 성향 분석하러 가기
                    </button>
                    <button class="popup-btn" type="button" @click="handleClose(true)">
                        닫기
                    </button>
                </div>
            </div>

            <!-- 내용 텍스트는 “이미지에 포함된 포스터”처럼 쓰는 게 레퍼런스랑 가장 유사합니다.
           만약 텍스트를 이미지 아래에 따로 두고 싶으면, popup-media 아래에 popup-body를 추가하면 됩니다. -->
        </div>
    </Teleport>
</template>

<script setup>
import { ref, watch } from "vue"

const props = defineProps({
    modelValue: { type: Boolean, default: false },
    storageKey: { type: String, default: "pb_promo_hide_until" },

    // ✅ 이미지 주입 가능 (요구사항: "사진 첨부 가능")
    imageSrc: { type: String, default: "" },
    imageAlt: { type: String, default: "promo" },
})

const emit = defineEmits(["update:modelValue", "survey"])

const dontShowToday = ref(false)

const todayKey = () => {
    const d = new Date()
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, "0")
    const day = String(d.getDate()).padStart(2, "0")
    return `${y}-${m}-${day}`
}

const hideForToday = () => {
    try {
        localStorage.setItem(props.storageKey, todayKey())
    } catch { }
}

const handleClose = (applyHide) => {
    // 체크박스 + 닫기 눌렀을 때만 오늘 숨김
    if (applyHide && dontShowToday.value) hideForToday()
    emit("update:modelValue", false)
}

const goSurvey = () => {
    // ✅ 레퍼런스에 맞추면 "이동"은 닫기와 별개
    // 원하면 여기서도 hideForToday() 할 수 있지만, 요구사항은 "체크+닫기"일 때만 숨김이므로 제거
    emit("update:modelValue", false)
    emit("survey")
}

watch(
    () => props.modelValue,
    (v) => {
        if (v) dontShowToday.value = false
    }
)
</script>

<style scoped>
/* 오버레이 */
.popup-overlay {
    position: fixed;
    inset: 0;
    z-index: 2000;
    display: grid;
    place-items: center;
    background: rgba(0, 0, 0, 0.60);
}

/* ✅ 레퍼런스 핵심: 각진 직사각형 + 고정 크기 */
.popup {
    position: relative;
    width: 480px;
    /* ✅ "조금 더 키워야" → 여기서 키움 */
    height: 640px;
    /* ✅ 세로 긴 포스터 */
    background: #000;
    box-shadow: 0 28px 80px rgba(0, 0, 0, 0.55);
    overflow: hidden;
    border-radius: 0;
    /* ✅ 각지게 */
}

/* 화면이 작으면 줄이되 비율 유지 */
@media (max-width: 620px) {
    .popup {
        width: 92vw;
        height: min(92vh, 720px);
    }
}

/* 이미지 영역: 버튼 70px 제외한 나머지 */
.popup-media {
    position: relative;
    width: 100%;
    height: calc(100% - 51px);
}

.popup-img,
.popup-img-fallback {
    width: 100%;
    height: 100%;
}

.popup-img {
    object-fit: cover;
    /* ✅ 포스터처럼 꽉 채움 */
    display: block;
}

.popup-img-fallback {
    display: grid;
    place-items: center;
    background: #111;
}

.fallback-text {
    color: rgba(255, 255, 255, 0.7);
    letter-spacing: 0.3em;
    font-weight: 700;
}

/* 레퍼런스처럼 위->아래 그라데이션 */
.popup-gradient {
    position: absolute;
    inset: 0;
    background: linear-gradient(to bottom,
            rgba(0, 0, 0, 0.40) 100%,
            rgba(0, 0, 0, 0.0) 45%,
            rgba(0, 0, 0, 0.70) 100%);
}

/* (옵션) 중앙 큰 타이틀용 */
.popup-center {
    position: absolute;
    top: 30%;
    left: 0;
    right: 0;
    text-align: center;
    pointer-events: none;
}

.popup-center-title {
    font-size: 56px;
    letter-spacing: 0.18em;
    font-weight: 900;
    color: #dc2626;
    text-shadow: 0 0 18px rgba(255, 255, 255, 0.65),
        2px 2px 4px rgba(0, 0, 0, 0.8),
        -1px -1px 0 #fff, 1px -1px 0 #fff,
        -1px 1px 0 #fff, 1px 1px 0 #fff;
}

/* 체크박스: 이미지 하단 좌측 */
.popup-check {
    position: absolute;
    left: 18px;
    bottom: 18px;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    color: #fff;
    font-size: 13px;
    cursor: pointer;
    user-select: none;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.6);
}

.popup-check input {
    width: 16px;
    height: 16px;
    cursor: pointer;
}

/* ✅ 하단 버튼 바: 70px 고정, 2분할 */
.popup-actions {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 50px;
    display: flex;
}

.popup-btn {
    flex: 1;
    border: 0;
    background: #000;
    color: #fff;
    font-weight: 500;
    font-size: 15px;
    cursor: pointer;
    transition: background 140ms ease;
}

.popup-btn.primary {
    background: #dc2626;
    border-right: 1px solid rgba(255, 255, 255, 0.20);
}

.popup-btn.primary:hover {
    background: #b91c1c;
}

.popup-btn:hover {
    background: #1f2937;
}

/* 텍스트 오버레이 컨테이너 */
.popup-copy {
  position: absolute;
  top: 45%;
  left: 32px;
  right: 32px;
  transform: translateY(-50%);
  z-index: 3;
  pointer-events: none;
  text-align: center;

  display: flex;
  flex-direction: column;
  gap: 14px;
}

.popup-pill {
  align-self: flex-start;
  margin-left: 75px;

  font-size: 15px;
  font-weight: 900;
  letter-spacing: 0.34em;

  color: #d61818;
  opacity: 1;

  -webkit-text-stroke: 0.6px rgba(0, 0, 0, 0.35);  /* 또는 아예 0px로 */

  /* ✅ 가독성: 어두운 그림자 + 붉은 글로우 */
  text-shadow:
    0 2px 0 rgba(0, 0, 0, 0.65),
    0 10px 18px rgba(0, 0, 0, 0.45),
    0 0 18px rgba(239, 68, 68, 0.35);

  /* 애니메이션(기존 유지 + 살짝 더 “튀게”) */
  animation:
    newEnter 520ms cubic-bezier(.2,.9,.2,1) 120ms both,
    newPulseRed 1400ms ease-in-out 900ms infinite;
}

@keyframes newEnter {
  from { transform: translateY(-10px) scale(0.92); opacity: 0; }
  to   { transform: translateY(0) scale(1); opacity: 1; }
}

@keyframes newPulseRed {
  0%, 100% {
    transform: translateY(0) scale(1);
    filter: drop-shadow(0 0 0 rgba(239, 68, 68, 0));
  }
  50% {
    transform: translateY(-1px) scale(1.06);
    filter: drop-shadow(0 0 10px rgba(239, 68, 68, 0.45));
  }
}


/* 헤드라인: 중앙 정렬 + 테두리 */
.popup-headline {
  margin: 0;
  font-size: 28px;
  font-weight: 900;
  line-height: 1.35;
  color: rgba(255, 255, 255, 0.92);

  text-align: center;
  letter-spacing: -0.02em;

  /* 윤곽선(테두리) */
  -webkit-text-stroke: 1.2px rgba(0, 0, 0, 0.55);

  /* stroke가 약한 브라우저 대비: 다중 shadow */
  text-shadow:
    0 3px 12px rgba(0, 0, 0, 0.65),
    0 0 26px rgba(255, 255, 255, 0.22);
}

/* 서브 카피: 중앙 정렬 + 얇은 테두리 */
.popup-lead {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.92);

  text-align: center;
  letter-spacing: -0.01em;

  -webkit-text-stroke: 0.8px rgba(0, 0, 0, 0.45);

  text-shadow:
    0 2px 10px rgba(0, 0, 0, 0.6),
    0 0 18px rgba(255, 255, 255, 0.18);
}


</style>
