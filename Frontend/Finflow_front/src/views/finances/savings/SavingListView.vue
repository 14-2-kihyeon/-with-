<template>
  <div class="page">
    <h1>적금 상품 목록</h1>

    <div class="toolbar">
      <label>은행 선택</label>
      <select v-model="selectedBank" @change="fetchList">
        <option value="">전체 은행</option>
        <option v-for="b in banks" :key="b" :value="b">{{ b }}</option>
      </select>

      <button @click="fetchList">조회</button>
      
      <!-- ✅ 동기화 버튼 -->
      <button 
        @click="syncData" 
        class="btn-sync"
        :disabled="syncing"
      >
        {{ syncing ? '동기화 중...' : '🔄 최신 데이터 가져오기' }}
      </button>
    </div>

    <!-- ✅ 동기화 메시지 -->
    <div v-if="syncMsg" class="sync-msg" :class="syncSuccess ? 'success' : 'error'">
      {{ syncMsg }}
    </div>

    <p v-if="err" class="err">{{ err }}</p>
    <p v-if="loading">로딩중...</p>

    <div v-else class="table-wrap">
      <table class="tbl">
        <thead>
          <tr>
            <th style="width: 60px;">No</th>
            <th style="width: 180px;">금융회사</th>
            <th>상품명</th>
            <th style="width: 180px;">상품코드</th>
            <th style="width: 90px;">옵션수</th>
          </tr>
        </thead>

        <tbody>
          <tr v-if="items.length === 0">
            <td colspan="5" class="empty">
              <div>데이터가 없습니다.</div>
              <button @click="syncData" class="btn-primary">
                데이터 불러오기
              </button>
            </td>
          </tr>

          <tr v-for="(p, idx) in items" :key="p.fin_prdt_cd">
            <td>{{ idx + 1 }}</td>
            <td>{{ p.kor_co_nm }}</td>
            <td>
              <RouterLink
                class="link"
                :to="{ name: 'saving_detail', params: { fin_prdt_cd: p.fin_prdt_cd } }"
              >
                {{ p.fin_prdt_nm }}
              </RouterLink>
            </td>
            <td class="mono">{{ p.fin_prdt_cd }}</td>
            <td style="text-align:center;">{{ (p.options || []).length }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { getSavingBanks, getSavings, syncSavings } from "@/api/finances"

const banks = ref([])
const selectedBank = ref("")
const items = ref([])
const loading = ref(false)
const err = ref("")

// ✅ 동기화 상태
const syncing = ref(false)
const syncMsg = ref("")
const syncSuccess = ref(false)

const fetchBanks = async () => {
  err.value = ""
  const data = await getSavingBanks()
  banks.value = data
}

const fetchList = async () => {
  loading.value = true
  err.value = ""
  try {
    const res = await getSavings(selectedBank.value)
    items.value = res.data
  } catch (e) {
    err.value = JSON.stringify(e.response?.data || e.message)
  } finally {
    loading.value = false
  }
}

// ✅ 동기화 함수
const syncData = async () => {
  syncing.value = true
  syncMsg.value = ""
  
  try {
    const result = await syncSavings()
    syncSuccess.value = true
    syncMsg.value = `✅ 동기화 완료! 상품 ${result.saved_products}개, 옵션 ${result.saved_options}개 저장됨`
    
    setTimeout(() => {
      syncMsg.value = ""
    }, 3000)
    
    await fetchBanks()
    await fetchList()
    
  } catch (e) {
    syncSuccess.value = false
    syncMsg.value = `❌ 동기화 실패: ${e.response?.data?.error || e.message}`
  } finally {
    syncing.value = false
  }
}

onMounted(async () => {
  await fetchBanks()
  await fetchList()
})
</script>

<style scoped>
/* 위와 동일한 스타일 */
</style>
