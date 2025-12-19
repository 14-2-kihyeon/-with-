<template>
  <div class="page">
    <h1>정기예금 상품 목록</h1>

    <div class="toolbar">
      <label>은행 선택</label>
      <select v-model="selectedBank" @change="loadDeposits">
        <option value="">전체</option>
        <option v-for="b in banks" :key="b" :value="b">{{ b }}</option>
      </select>

      <button @click="loadDeposits">조회</button>
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
          <tr v-if="products.length === 0">
            <td colspan="4" class="empty">데이터가 없습니다.</td>
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
import { getBanks, getDeposits } from "@/api/finances"

const banks = ref([])
const selectedBank = ref("")
const products = ref([])
const loading = ref(false)
const errorMsg = ref("")

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

onMounted(async () => {
  await loadBanks()
  await loadDeposits()
})
</script>


<style scoped>

</style>