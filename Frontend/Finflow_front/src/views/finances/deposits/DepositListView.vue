<template>
  <div class="page">
    <h1>정기예금 상품 목록</h1>

    <!-- ✅ 동기화 버튼 추가 -->
    <div class="toolbar">
      <label>은행 선택</label>
      <select v-model="selectedBank" @change="loadDeposits">
        <option value="">전체</option>
        <option v-for="b in banks" :key="b" :value="b">{{ b }}</option>
      </select>

      <button @click="loadDeposits">조회</button>
      
      <!-- ✅ 새로 추가 -->
      <button 
        @click="syncDeposits" 
        class="btn-sync"
        :disabled="syncing"
      >
        {{ syncing ? '동기화 중...' : '🔄 최신 데이터 가져오기' }}
      </button>
    </div>

    <!-- ✅ 동기화 결과 메시지 -->
    <div v-if="syncMsg" class="sync-msg" :class="syncSuccess ? 'success' : 'error'">
      {{ syncMsg }}
    </div>

    <p v-if="errorMsg" class="err">{{ errorMsg }}</p>
    <p v-if="loading">불러오는 중...</p>

    <div v-else class="table-wrap">
      <table class="tbl">
        <thead>
          <tr>
            <th style="width: 60px;">No</th>
            <th style="width: 180px;">금융회사</th>
            <th>상품명</th>
            <th style="width: 180px;">상품코드</th>
          </tr>
        </thead>
        <tbody>
          <!-- ✅ 빈 데이터일 때 안내 개선 -->
          <tr v-if="products.length === 0">
            <td colspan="4" class="empty">
              <div>데이터가 없습니다.</div>
              <button @click="syncDeposits" class="btn-primary">
                데이터 불러오기
              </button>
            </td>
          </tr>

          <tr v-for="(p, idx) in products" :key="p.fin_prdt_cd">
            <td>{{ idx + 1 }}</td>
            <td>{{ p.kor_co_nm }}</td>
            <td>
              <RouterLink
                class="link"
                :to="{ name: 'deposit_detail', params: { fin_prdt_cd: p.fin_prdt_cd } }"
              >
                {{ p.fin_prdt_nm }}
              </RouterLink>
            </td>
            <td class="mono">{{ p.fin_prdt_cd }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { getBanks, getDeposits, syncDeposits as apiSyncDeposits } from "@/api/finances"

const banks = ref([])
const selectedBank = ref("")
const products = ref([])
const loading = ref(false)
const errorMsg = ref("")

// ✅ 동기화 관련 상태
const syncing = ref(false)
const syncMsg = ref("")
const syncSuccess = ref(false)

const loadBanks = async () => {
  try {
    banks.value = await getBanks()
  } catch (e) {
    errorMsg.value = "은행 목록을 불러오지 못했어요."
  }
}

const loadDeposits = async () => {
  loading.value = true
  errorMsg.value = ""
  try {
    products.value = await getDeposits(selectedBank.value)
  } catch (e) {
    errorMsg.value = "상품 목록을 불러오지 못했어요."
  } finally {
    loading.value = false
  }
}

// ✅ 동기화 함수 추가
const syncDeposits = async () => {
  syncing.value = true
  syncMsg.value = ""
  
  try {
    const result = await apiSyncDeposits()
    syncSuccess.value = true
    syncMsg.value = `✅ 동기화 완료! 상품 ${result.saved_products}개, 옵션 ${result.saved_options}개 저장됨`
    
    // 3초 후 메시지 제거
    setTimeout(() => {
      syncMsg.value = ""
    }, 3000)
    
    // 목록 새로고침
    await loadBanks()
    await loadDeposits()
    
  } catch (e) {
    syncSuccess.value = false
    syncMsg.value = `❌ 동기화 실패: ${e.response?.data?.error || e.message}`
  } finally {
    syncing.value = false
  }
}

onMounted(async () => {
  await loadBanks()
  await loadDeposits()
})
</script>

<style scoped>
.page {
  padding: 16px;
}

.toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin: 12px 0;
}

.btn-sync {
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.btn-sync:hover:not(:disabled) {
  background: #218838;
}

.btn-sync:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}

.btn-primary:hover {
  background: #0056b3;
}

.sync-msg {
  padding: 12px;
  margin: 10px 0;
  border-radius: 4px;
  font-weight: bold;
}

.sync-msg.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.sync-msg.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.table-wrap {
  overflow-x: auto;
}

.tbl {
  width: 100%;
  border-collapse: collapse;
}

.tbl th,
.tbl td {
  border: 1px solid #ddd;
  padding: 10px;
  vertical-align: top;
}

.tbl th {
  background: #f7f7f7;
  text-align: left;
}

.empty {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.err {
  color: #c00;
  white-space: pre-wrap;
}

.link {
  text-decoration: underline;
  color: #007bff;
}

.link:hover {
  color: #0056b3;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
}
</style>