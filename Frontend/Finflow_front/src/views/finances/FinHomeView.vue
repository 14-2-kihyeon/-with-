<template>
  <div class="page">
    <h1 class="mb-3">예적금</h1>
    <p class="text-muted mb-4">원하는 상품 유형을 선택하면 최신 데이터를 확인한 뒤 목록으로 이동합니다.</p>

    <div class="d-flex gap-2 flex-wrap">
      <button class="btn btn-primary px-4" :disabled="loading" @click="goDeposits">
        <span v-if="loading && target==='deposits'" class="spinner-border spinner-border-sm me-2"></span>
        예금 보러가기
      </button>

      <button class="btn btn-outline-primary px-4" :disabled="loading" @click="goSavings">
        <span v-if="loading && target==='savings'" class="spinner-border spinner-border-sm me-2"></span>
        적금 보러가기
      </button>
    </div>

    <div v-if="msg" class="alert mt-4" :class="ok ? 'alert-success' : 'alert-danger'">
      {{ msg }}
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import {
  // 예금
  getBanks, getDeposits, syncDeposits as apiSyncDeposits,
  // 적금
  getSavingBanks, getSavings, syncSavings
} from "@/api/finances"

const router = useRouter()

const loading = ref(false)
const target = ref("") // 'deposits' | 'savings'
const msg = ref("")
const ok = ref(true)

// “데이터가 비어있으면 동기화” 전략 (불필요한 동기화 방지)
const ensureDepositsReady = async () => {
  // 1) 조회로 데이터 있는지 먼저 확인(전체)
  const list = await getDeposits("")
  if (Array.isArray(list) && list.length > 0) return

  // 2) 없으면 동기화
  await apiSyncDeposits()

  // 3) 동기화 후 한번 더 확인
  await getBanks()
  const list2 = await getDeposits("")
  if (!Array.isArray(list2) || list2.length === 0) {
    throw new Error("예금 데이터가 아직 없습니다.")
  }
}

const ensureSavingsReady = async () => {
  // saving쪽은 getSavings가 res.data 구조이므로 현재 코드 기준 맞춤
  const res = await getSavings("")
  const items = res?.data ?? []
  if (Array.isArray(items) && items.length > 0) return

  await syncSavings()
  await getSavingBanks()

  const res2 = await getSavings("")
  const items2 = res2?.data ?? []
  if (!Array.isArray(items2) || items2.length === 0) {
    throw new Error("적금 데이터가 아직 없습니다.")
  }
}

const goDeposits = async () => {
  loading.value = true
  target.value = "deposits"
  msg.value = ""
  try {
    await ensureDepositsReady()
    router.push({ name: "deposit_list" })
  } catch (e) {
    ok.value = false
    msg.value = `예금 데이터 준비 실패: ${e?.message || e}`
  } finally {
    loading.value = false
    target.value = ""
  }
}

const goSavings = async () => {
  loading.value = true
  target.value = "savings"
  msg.value = ""
  try {
    await ensureSavingsReady()
    router.push({ name: "saving_list" })
  } catch (e) {
    ok.value = false
    msg.value = `적금 데이터 준비 실패: ${e?.message || e}`
  } finally {
    loading.value = false
    target.value = ""
  }
}
</script>

<style scoped>
.page { padding: 16px; }
</style>
