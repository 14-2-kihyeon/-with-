<template>
  <section class="bankmap-wrap">
    <h2>은행 찾기 지도</h2>

    <div class="bankmap-layout">
      <div class="bankmap-controls">
        <div class="control-group">
          <label>출발지</label>
          <div class="row">
            <input v-model.trim="originKeyword" placeholder="예: 서울 강남역, 부산역" />
            <button @click="onSetOrigin">설정</button>
          </div>
          <button class="search-btn" @click="onMyLocation">내 위치로 설정</button>
        </div>

        <div class="control-group">
          <label>시/도</label>
          <select v-model="selectedSido" @change="onSidoChange">
            <option value="">시/도를 선택하세요</option>
            <option v-for="s in sidoList" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>

        <div class="control-group">
          <label>시/군/구</label>
          <select v-model="selectedGugun" :disabled="!gugunList.length">
            <option value="">시/군/구를 선택하세요</option>
            <option v-for="g in gugunList" :key="g" :value="g">{{ g }}</option>
          </select>
        </div>

        <div class="control-group">
          <label>은행</label>
          <select v-model="selectedBank">
            <option value="">은행을 선택하세요</option>
            <option v-for="b in bankList" :key="b" :value="b">{{ b }}</option>
          </select>
        </div>

        <button class="search-btn" @click="searchBanks">검색</button>
        <p class="hint">※ 검색 결과 마커를 클릭하면 길찾기 경로를 표시합니다.</p>
      </div>

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
  initSelectData() // ✅ 이거 꼭!

  // ✅ 처음 진입하면 내 위치로 지도 중심 이동 + 마커 고정
  try {
    await requestMyLocation()
  } catch (e) {
    console.warn("내 위치 권한 거부/실패:", e)
    // 권한 거부면 그냥 기본 중심(부산 등)으로 남겨둠
  }
})
</script>

<style scoped>
.bankmap-layout { display: flex; gap: 16px; }
.bankmap-controls { width: 320px; }
.bankmap-map { flex: 1; min-height: 520px; }
.map { width: 100%; height: 520px; border-radius: 8px; }
.control-group { margin-bottom: 12px; display: flex; flex-direction: column; gap: 6px; }
.control-group .row { display: flex; gap: 8px; }
.search-btn { width: 100%; padding: 10px 12px; margin-top: 6px; }
.hint { font-size: 12px; opacity: 0.8; margin-top: 8px; }
</style>
