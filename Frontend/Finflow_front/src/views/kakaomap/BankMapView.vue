<template>
  <section class="bankmap-wrap">
    <!-- 헤더 -->
    <div class="bankmap-header">
      <div class="header-title">
        <span class="icon">🏦</span>
        <h2>은행 찾기</h2>
      </div>
    </div>

    <!-- 메인 레이아웃 -->
    <div class="bankmap-layout">
      <!-- 왼쪽 컨트롤 패널 -->
      <div class="bankmap-controls">
        <!-- 출발지 설정 카드 -->
        <div class="control-card">
          <div class="card-header">
            <span class="card-icon">📍</span>
            <h3>출발지</h3>
          </div>
          <div class="input-group">
            <input 
              v-model.trim="originKeyword" 
              placeholder="예: 서울 강남역, 부산역"
              class="input-field"
            />
            <button @click="onSetOrigin" class="btn-primary btn-sm">설정</button>
          </div>
          <button @click="onMyLocation" class="btn-outline">
            <span class="btn-icon">📌</span>
            내 위치로 설정
          </button>
        </div>

        <!-- 검색 조건 카드 -->
        <div class="control-card">
          <div class="card-header">
            <span class="card-icon">🔍</span>
            <h3>검색 조건</h3>
          </div>
          
          <div class="select-group">
            <label>시/도</label>
            <select v-model="selectedSido" @change="onSidoChange" class="select-field">
              <option value="">시/도를 선택하세요</option>
              <option v-for="s in sidoList" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>

          <div class="select-group">
            <label>시/군/구</label>
            <select 
              v-model="selectedGugun" 
              :disabled="!gugunList.length"
              class="select-field"
            >
              <option value="">시/군/구를 선택하세요</option>
              <option v-for="g in gugunList" :key="g" :value="g">{{ g }}</option>
            </select>
          </div>

          <div class="select-group">
            <label>은행</label>
            <select v-model="selectedBank" class="select-field">
              <option value="">은행을 선택하세요</option>
              <option v-for="b in bankList" :key="b" :value="b">{{ b }}</option>
            </select>
          </div>

          <button @click="searchBanks" class="btn-primary">
            <span class="btn-icon">🔍</span>
            검색하기
          </button>
          
          <p class="hint">
            <span class="hint-icon">💡</span>
            검색 결과 마커를 클릭하면 길찾기 경로를 표시합니다.
          </p>
        </div>
      </div>

      <!-- 오른쪽 지도 -->
      <div class="bankmap-map">
        <div ref="mapEl" class="map"></div>
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
    alert("내 위치를 가져오지 못했습니다. (브라우저 권한 확인)")
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
    console.warn("내 위치 권한 거부/실패:", e)
  }
})
</script>

<style scoped>
/* 전체 래퍼 */
.bankmap-wrap {
  max-width: 1280px;
  margin: 0 auto;
  padding: 20px;
  background: #f9fafb;
  min-height: 100vh;
}

/* 헤더 */
.bankmap-header {
  background: #3182f6;
  border-radius: 16px;
  padding: 20px 28px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-title .icon {
  font-size: 1.5rem;
}

.header-title h2 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  color: #ffffff;
}

/* 메인 레이아웃 */
.bankmap-layout {
  display: flex;
  gap: 16px;
}

/* 왼쪽 컨트롤 패널 */
.bankmap-controls {
  width: 340px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 컨트롤 카드 */
.control-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e8eb;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e8eb;
}

.card-icon {
  font-size: 1.2rem;
}

.card-header h3 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 600;
  color: #191f28;
}

/* 입력 그룹 */
.input-group {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.input-field {
  flex: 1;
  padding: 11px 14px;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  font-size: 0.95rem;
  color: #191f28;
  transition: all 0.15s ease;
  background: #ffffff;
}

.input-field:focus {
  outline: none;
  border-color: #3182f6;
  box-shadow: 0 0 0 3px rgba(49, 130, 246, 0.1);
}

.input-field::placeholder {
  color: #9ca3af;
}

/* 셀렉트 그룹 */
.select-group {
  margin-bottom: 14px;
}

.select-group label {
  display: block;
  font-size: 0.9rem;
  font-weight: 500;
  color: #4b5563;
  margin-bottom: 6px;
}

.select-field {
  width: 100%;
  padding: 11px 14px;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  font-size: 0.95rem;
  color: #191f28;
  background: #ffffff;
  cursor: pointer;
  transition: all 0.15s ease;
}

.select-field:hover:not(:disabled) {
  border-color: #9ca3af;
}

.select-field:focus {
  outline: none;
  border-color: #3182f6;
  box-shadow: 0 0 0 3px rgba(49, 130, 246, 0.1);
}

.select-field:disabled {
  background: #f3f4f6;
  color: #9ca3af;
  cursor: not-allowed;
}

/* 버튼 스타일 */
.btn-primary {
  width: 100%;
  padding: 13px 20px;
  border: none;
  border-radius: 10px;
  background: #3182f6;
  color: #ffffff;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.btn-primary:hover {
  background: #1d6ee0;
}

.btn-primary:active {
  transform: scale(0.98);
}

.btn-primary.btn-sm {
  width: auto;
  padding: 11px 18px;
  font-size: 0.9rem;
}

.btn-outline {
  width: 100%;
  padding: 11px 20px;
  border: 1.5px solid #d1d5db;
  border-radius: 10px;
  background: #ffffff;
  color: #4b5563;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.btn-outline:hover {
  border-color: #3182f6;
  color: #3182f6;
  background: #f8fafc;
}

.btn-outline:active {
  transform: scale(0.98);
}

.btn-icon {
  font-size: 1rem;
}

/* 힌트 텍스트 */
.hint {
  margin-top: 14px;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #6b7280;
  line-height: 1.5;
  display: flex;
  align-items: flex-start;
  gap: 6px;
  border: 1px solid #e5e8eb;
}

.hint-icon {
  font-size: 0.9rem;
  flex-shrink: 0;
  margin-top: 1px;
}

/* 지도 영역 */
.bankmap-map {
  flex: 1;
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e8eb;
  min-height: 600px;
}

.map {
  width: 100%;
  height: 600px;
}

/* 반응형 */
@media (max-width: 968px) {
  .bankmap-wrap {
    padding: 12px;
  }

  .bankmap-header {
    padding: 16px 20px;
  }

  .header-title h2 {
    font-size: 1.15rem;
  }

  .bankmap-layout {
    flex-direction: column;
  }

  .bankmap-controls {
    width: 100%;
  }

  .bankmap-map {
    min-height: 400px;
  }

  .map {
    height: 400px;
  }
}

@media (max-width: 640px) {
  .input-group {
    flex-direction: column;
  }

  .btn-primary.btn-sm {
    width: 100%;
  }

  .control-card {
    padding: 16px;
  }

  .card-header h3 {
    font-size: 1rem;
  }
}

/* 포커스 스타일 */
button:focus,
input:focus,
select:focus {
  outline: 2px solid #3182f6;
  outline-offset: 2px;
}

/* 애니메이션 */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.control-card {
  animation: slideIn 0.3s ease-out;
}
</style>