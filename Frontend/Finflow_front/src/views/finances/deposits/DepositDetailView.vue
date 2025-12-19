<template>
  <div class="page">
    <h1>정기예금 상세</h1>

    <p v-if="errorMsg" class="err">{{ errorMsg }}</p>
    <p v-if="loading">불러오는 중...</p>

    <div v-if="product && !loading">
      <h3>상품 정보</h3>
      <div class="table-wrap">
        <table class="tbl">
          <tbody>
            <tr><th style="width:180px;">은행</th><td>{{ product.kor_co_nm }}</td></tr>
            <tr><th>상품명</th><td>{{ product.fin_prdt_nm }}</td></tr>
            <tr><th>상품코드</th><td class="mono">{{ product.fin_prdt_cd }}</td></tr>
            <tr><th>가입방법</th><td>{{ product.join_way || "-" }}</td></tr>
            <tr><th>가입대상</th><td>{{ product.join_member || "-" }}</td></tr>
            <tr><th>우대조건</th><td>{{ product.spcl_cnd || "-" }}</td></tr>
          </tbody>
        </table>
      </div>

      <hr />

      <h3>금리 옵션</h3>
      <div class="table-wrap">
        <table class="tbl">
          <thead>
            <tr>
              <th style="width:120px;">기간(개월)</th>
              <th style="width:120px;">기본금리</th>
              <th style="width:120px;">최고금리</th>
              <th>유형</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="(product.options || []).length === 0">
              <td colspan="4" class="empty">옵션이 없습니다.</td>
            </tr>

            <tr v-for="(o, idx) in product.options" :key="idx">
              <td style="text-align:center;">{{ o.save_trm }}</td>
              <td style="text-align:right;">{{ formatRate(o.intr_rate) }}</td>
              <td style="text-align:right;">{{ formatRate(o.intr_rate2) }}</td>
              <td>{{ o.rsrv_type || "-" }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div style="margin-top: 14px;">
        <RouterLink class="link" :to="{ name: 'deposit_list' }">← 목록으로</RouterLink>
      </div>
    </div>
  </div>
</template>


<script setup>
import { ref, onMounted, watch } from "vue"
import { useRoute } from "vue-router"
import { getDepositDetail } from "@/api/finances"

const route = useRoute()
const product = ref(null)
const loading = ref(false)
const errorMsg = ref("")

const formatRate = (v) => {
  if (v === null || v === undefined) return "-"
  if (Number(v) < 0) return "정보없음"
  return `${v}%`
}

const loadDetail = async () => {
  loading.value = true
  errorMsg.value = ""
  try {
    product.value = await getDepositDetail(route.params.fin_prdt_cd)
  } catch (e) {
    errorMsg.value = "상세 정보를 불러오지 못했어요."
  } finally {
    loading.value = false
  }
}

onMounted(loadDetail)
watch(() => route.params.fin_prdt_cd, loadDetail)
</script>


<style scoped>

</style>