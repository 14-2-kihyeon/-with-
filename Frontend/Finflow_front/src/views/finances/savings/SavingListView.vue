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
            <td colspan="5" class="empty">데이터가 없습니다.</td>
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
import { getSavingBanks, getSavings } from "@/api/finances"

const banks = ref([])
const selectedBank = ref("")
const items = ref([])
const loading = ref(false)
const err = ref("")

const fetchBanks = async () => {
  err.value = ""
  const data = await getSavingBanks()
  // banks API가 문자열 배열이라고 가정
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

onMounted(async () => {
  await fetchBanks()
  await fetchList()
})
</script>

<style scoped>
.page { padding: 16px; }
.toolbar { display:flex; gap:10px; align-items:center; margin: 12px 0; }
.table-wrap { overflow-x: auto; }
.tbl { width: 100%; border-collapse: collapse; }
.tbl th, .tbl td { border: 1px solid #ddd; padding: 10px; vertical-align: top; }
.tbl th { background: #f7f7f7; text-align: left; }
.empty { text-align: center; padding: 20px; color: #666; }
.err { color: #c00; white-space: pre-wrap; }
.link { text-decoration: underline; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }
</style>
