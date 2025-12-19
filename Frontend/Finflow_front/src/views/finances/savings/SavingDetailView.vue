<template>
  <div class="page">
    <h1>적금 상품 상세</h1>

    <p v-if="err" class="err">{{ err }}</p>
    <p v-if="loading">로딩중...</p>

    <div v-else-if="product">
      <!-- ✅ 상품 기본 정보 테이블 -->
      <h3>상품 정보</h3>
      <div class="table-wrap">
        <table class="tbl">
          <tbody>
            <tr>
              <th style="width: 180px;">금융회사</th>
              <td>{{ product.kor_co_nm }}</td>
            </tr>
            <tr>
              <th>상품명</th>
              <td>{{ product.fin_prdt_nm }}</td>
            </tr>
            <tr>
              <th>상품코드</th>
              <td class="mono">{{ product.fin_prdt_cd }}</td>
            </tr>
            <tr>
              <th>가입방법</th>
              <td>{{ product.join_way }}</td>
            </tr>
            <tr>
              <th>가입대상</th>
              <td>{{ product.join_member }}</td>
            </tr>
            <tr>
              <th>우대조건</th>
              <td>{{ product.spcl_cnd }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <hr />

      <!-- ✅ 옵션 테이블 -->
      <h3>금리 옵션</h3>
      <div class="table-wrap">
        <table class="tbl">
          <thead>
            <tr>
              <th style="width: 120px;">저축기간(개월)</th>
              <th style="width: 140px;">적립유형</th>
              <th style="width: 120px;">기본금리</th>
              <th style="width: 120px;">최고금리</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="options.length === 0">
              <td colspan="4" class="empty">옵션이 없습니다.</td>
            </tr>

            <tr v-for="(o, idx) in options" :key="o.id || `${o.save_trm}-${o.rsrv_type}-${idx}`">
              <td style="text-align:center;">{{ o.save_trm }}</td>
              <td>{{ o.rsrv_type || "-" }}</td>
              <td style="text-align:right;">{{ displayRate(o.intr_rate) }}</td>
              <td style="text-align:right;">{{ displayRate(o.intr_rate2) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div style="margin-top: 14px;">
        <RouterLink class="link" :to="{ name: 'saving_list' }">← 목록으로</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue"
import { useRoute } from "vue-router"
import { getSavingDetail } from "@/api/finances"

const route = useRoute()
const loading = ref(false)
const err = ref("")
const product = ref(null)

const options = computed(() => {
  const p = product.value
  if (!p) return []
  // 백엔드 serializer에서 options로 내려준다고 가정 (혹시 다르면 여기만 바꾸면 됨)
  const list = p.options || []
  // 보기 좋게 정렬(기간 오름차순, 최고금리 내림차순)
  return [...list].sort((a, b) => {
    if (Number(a.save_trm) !== Number(b.save_trm)) return Number(a.save_trm) - Number(b.save_trm)
    return Number(b.intr_rate2) - Number(a.intr_rate2)
  })
})

const displayRate = (v) => {
  if (v === null || v === undefined) return "-"
  // 너는 -1로 저장한 케이스가 있어서 처리
  if (Number(v) < 0) return "-"
  return `${v}%`
}

onMounted(async () => {
  loading.value = true
  err.value = ""
  try {
    const fin_prdt_cd = route.params.fin_prdt_cd
    const res = await getSavingDetail(fin_prdt_cd)
    product.value = res.data
  } catch (e) {
    err.value = JSON.stringify(e.response?.data || e.message)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page { padding: 16px; }
.table-wrap { overflow-x: auto; margin-top: 8px; }
.tbl { width: 100%; border-collapse: collapse; }
.tbl th, .tbl td { border: 1px solid #ddd; padding: 10px; vertical-align: top; }
.tbl thead th { background: #f7f7f7; text-align: left; }
.tbl tbody th { background: #fafafa; text-align: left; }
.empty { text-align: center; padding: 20px; color: #666; }
.err { color: #c00; white-space: pre-wrap; }
.link { text-decoration: underline; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }
</style>
