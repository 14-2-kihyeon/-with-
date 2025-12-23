<template>
  <section class="bankmap-wrap">
    <div class="bankmap-header">
      <h2 class="header-title">주변 은행 찾기</h2>
      <p class="header-desc">원하는 지역을 선택하고 주거래은행의 위치를 쉽고 빠르게 확인하세요.</p>
    </div>

    <div class="bankmap-layout">
      <aside class="bankmap-controls">
        
        <div class="control-card">
          <div class="card-title-row">
            <span class="icon-circle"></span>
            <h3>위치 기준 설정</h3>
          </div>
          
          <div class="search-input-box">
            <input 
              v-model.trim="originKeyword" 
              placeholder="예: 강남역, 판교역"
              class="input-field"
              @keyup.enter="onSetOrigin"
            />
            <button @click="onSetOrigin" class="btn-text">설정</button>
          </div>
          
          <button @click="onMyLocation" class="btn-location">
            현재 내 위치로 설정하기
          </button>
        </div>

        <div class="control-card">
          <div class="card-title-row">
            <span class="icon-circle"></span>
            <h3>조건 검색</h3>
          </div>
          
          <div class="form-row">
            <div class="select-group">
              <label>시/도</label>
              <div class="custom-select">
                <select v-model="selectedSido" @change="onSidoChange">
                  <option value="">전체</option>
                  <option v-for="s in sidoList" :key="s" :value="s">{{ s }}</option>
                </select>
              </div>
            </div>

            <div class="select-group">
              <label>시/군/구</label>
              <div class="custom-select">
                <select 
                  v-model="selectedGugun" 
                  :disabled="!gugunList.length"
                >
                  <option value="">전체</option>
                  <option v-for="g in gugunList" :key="g" :value="g">{{ g }}</option>
                </select>
              </div>
            </div>
          </div>

          <div class="select-group mt-large">
            <label>은행 선택</label>
            <div class="custom-select">
              <select v-model="selectedBank">
                <option value="">모든 은행 보기</option>
                <option v-for="b in bankList" :key="b" :value="b">{{ b }}</option>
              </select>
            </div>
          </div>

          <button @click="searchBanks" class="btn-search-primary">
            검색하기
          </button>
          
          <div class="ux-tip">
            <span class="tip-icon">💡</span>
            <p>지도에서 <strong>마커를 클릭</strong>하면<br> 길찾기가 시작됩니다.</p>
          </div>
        </div>
      </aside>

      <div class="bankmap-map-wrapper">
        <div ref="mapEl" class="map-canvas"></div>
        </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue"
import { useKakaoBankMap } from "@/composables/kakaomap/useKakaoBankMap"

const mapEl = ref(null)
const originKeyword = ref("")

const {
  loadKakaoSdk,
  initMap,
  loadBankMapData,
  initSelectData,

  selectedSido, selectedGugun, selectedBank,
  sidoList, gugunList, bankList,
  onSidoChange,

  setOriginByKeyword,
  searchBanks,
  requestMyLocation,
} = useKakaoBankMap()

const onSetOrigin = () => {
  if (!originKeyword.value) return alert("출발지를 입력해주세요.")
  setOriginByKeyword(originKeyword.value)
}

const onMyLocation = async () => {
  try {
    await requestMyLocation()
  } catch (e) {
    console.error(e)
    alert("위치 정보를 가져올 수 없습니다. 브라우저 권한을 확인해주세요.")
  }
}

onMounted(async () => {
  await loadKakaoSdk()
  initMap(mapEl.value)
  await loadBankMapData()
  initSelectData()
  
  try {
    await requestMyLocation()
  } catch (e) {
    // 조용히 실패 (사용자가 권한 거부 시 에러 창 띄우지 않음)
  }
})
</script>

<style scoped>
/* Reset */
* { box-sizing: border-box; }

.bankmap-wrap {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
  min-height: 100vh;
  color: #191F28;
  font-family: -apple-system, BlinkMacSystemFont, "Pretendard", sans-serif;
}

/* --- Header --- */
.bankmap-header {
  margin-bottom: 32px;
}
.header-title {
  font-size: 32px;
  font-weight: 800;
  color: #191F28;
  margin: 0 0 12px 0;
  letter-spacing: -0.5px;
}
.header-desc {
  font-size: 17px;
  color: #6B7684;
  margin: 0;
  line-height: 1.5;
}

/* --- Layout --- */
.bankmap-layout {
  display: flex;
  gap: 28px;
  height: 680px; /* 넉넉한 높이 */
}

.bankmap-controls {
  width: 340px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* --- Cards (Neumorphism 느낌을 뺀 깔끔한 Flat Style) --- */
.control-card {
  background: #fff;
  border-radius: 20px;
  padding: 24px;
  /* 부드럽고 고급스러운 그림자 */
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0,0,0,0.03); 
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}
.icon-circle {
  font-size: 18px;
}
.card-title-row h3 {
  font-size: 18px;
  font-weight: 700;
  color: #333D4B;
  margin: 0;
}

/* --- 고급스러운 Input Field --- */
.search-input-box {
  display: flex;
  align-items: center;
  background-color: #F2F4F6;
  border-radius: 12px;
  padding: 6px 16px; /* 높이 확보 */
  transition: all 0.2s;
  margin-bottom: 12px;
}
.search-input-box:focus-within {
  background-color: #fff;
  box-shadow: 0 0 0 2px #3182F6 inset; /* 내부 파란 테두리 */
}
.input-field {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 16px;
  padding: 12px 0;
  color: #191F28;
  outline: none;
}
.input-field::placeholder {
  color: #B0B8C1;
}

.btn-text {
  background: none;
  border: none;
  color: #3182F6;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  padding: 8px;
  margin-right: -8px;
}
.btn-text:hover {
  color: #1B64DA;
}

/* 내 위치 버튼 */
.btn-location {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px;
  background-color: #fff;
  border: 1px solid #E5E8EB;
  border-radius: 12px;
  color: #4E5968;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}
.btn-location:hover {
  background-color: #F9FAFB;
  border-color: #D1D6DB;
  color: #333D4B;
}

/* --- Custom Select Dropdown (핵심) --- */
.form-row {
  display: flex;
  gap: 12px;
}
.select-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.select-group label {
  font-size: 13px;
  font-weight: 600;
  color: #8B95A1;
  margin-left: 4px;
}

.custom-select {
  position: relative;
  width: 100%;
  background-color: #F2F4F6;
  border-radius: 12px;
  transition: all 0.2s;
}
.custom-select:hover {
  background-color: #EAECEF;
}
/* 브라우저 기본 화살표 제거하고 커스텀 화살표 적용 */
.custom-select select {
  width: 100%;
  padding: 14px 16px; /* 넉넉한 터치 영역 */
  border: none;
  background: transparent;
  border-radius: 12px;
  font-size: 15px;
  color: #333D4B;
  outline: none;
  appearance: none; /* 기본 스타일 제거 */
  -webkit-appearance: none;
  cursor: pointer;
  
  /* 커스텀 화살표 (SVG Data URI) */
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%238B95A1' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 16px;
}
.custom-select:focus-within {
  box-shadow: 0 0 0 2px #3182F6 inset;
  background-color: #fff;
}
.custom-select select:disabled {
  color: #C5C8CE;
  cursor: not-allowed;
}

.mt-large { margin-top: 20px; }

/* 검색 버튼 */
.btn-search-primary {
  margin-top: 24px;
  width: 100%;
  padding: 16px;
  background-color: #3182F6;
  color: #fff;
  border: none;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.1s, background-color 0.2s;
  box-shadow: 0 4px 12px rgba(49, 130, 246, 0.25); /* 버튼 그림자 */
}
.btn-search-primary:hover {
  background-color: #1B64DA;
}
.btn-search-primary:active {
  transform: scale(0.98);
}

/* UX 팁 박스 */
.ux-tip {
  margin-top: 20px;
  padding: 14px 16px;
  background-color: #F9FAFB;
  border-radius: 12px;
  display: flex;
  gap: 10px;
  align-items: center;
}
.tip-icon { font-size: 18px; }
.ux-tip p {
  margin: 0;
  font-size: 13px;
  color: #6B7684;
  line-height: 1.4;
}
.ux-tip strong {
  color: #3182F6;
  font-weight: 600;
}

/* --- Map Area --- */
.bankmap-map-wrapper {
  flex: 1;
  border-radius: 20px;
  overflow: hidden;
  /* 지도가 떠있는 느낌 */
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08); 
  border: 1px solid rgba(0,0,0,0.02);
  background-color: #fff;
}
.map-canvas {
  width: 100%;
  height: 100%;
}

/* Mobile */
@media (max-width: 900px) {
  .bankmap-layout {
    flex-direction: column;
    height: auto;
  }
  .bankmap-controls {
    width: 100%;
  }
  .bankmap-map-wrapper {
    height: 400px;
  }
}
</style>

<style>
.map-origin-label {
  background-color: #3182F6; /* 파란색으로 통일하여 신뢰감 상승 */
  color: #fff;
  padding: 10px 16px;
  border-radius: 30px;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: -0.2px;
  box-shadow: 0 4px 12px rgba(49, 130, 246, 0.4);
  transform: translateY(-48px);
  white-space: nowrap;
  border: 2px solid #fff;
}
/* 말풍선 꼬리 */
.map-origin-label::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  border-width: 6px 6px 0;
  border-style: solid;
  border-color: #3182F6 transparent transparent transparent;
}
</style>