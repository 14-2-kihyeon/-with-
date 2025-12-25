<template>
  <div class="fin-page">
    <!-- Alert Modal -->
    <AlertModal
      v-model="showAlert"
      :icon="alertConfig.icon"
      :title="alertConfig.title"
      :message="alertConfig.message"
      :confirm-text="alertConfig.confirmText"
      @confirm="alertConfig.onConfirm"
    />

    <div class="fin-shell">
      <!-- 상단 안내(선택) -->
      <div class="fin-notice">
        <span class="fin-notice__text">원하는 상품을 선택하고 <span class="fin-notice__hl">금리와 만기</span>를 비교해보세요.</span>
      </div>
      <div class="fin-tabs-wrap">
        <!-- 탭: 예금/적금/현물 -->
        <div class="fin-tabs" role="tablist" aria-label="예적금 탭">
          <button
            class="fin-tab"
            :class="{ active: activeTab === 'deposit' }"
            type="button"
            role="tab"
            :aria-selected="activeTab === 'deposit'"
            @click="setTab('deposit')"
          >
            예금
          </button>
          <button
            class="fin-tab"
            :class="{ active: activeTab === 'saving' }"
            type="button"
            role="tab"
            :aria-selected="activeTab === 'saving'"
            @click="setTab('saving')"
          >
            적금
          </button>
          <button
            class="fin-tab"
            type="button"
            role="tab"
            aria-selected="false"
            @click="goGoldSilver"
          >
            현물
          </button>
        </div>
      </div>
      <!-- 은행 슬라이더 영역 -->
      <div class="bank-panel">
        <div class="bank-panel__inner">
          <button
            class="bank-nav bank-nav--left"
            type="button"
            :disabled="bankPage === 0"
            @click="bankPrev"
            aria-label="이전 은행"
          >
            ‹
          </button>

          <div class="bank-row" role="list" aria-label="은행 목록">
            <button
              v-for="b in visibleBanks"
              :key="b.key"
              type="button"
              class="bank-card bank-card--mini"
              :class="{ selected: selectedBankKeysSet.has(b.key) }"
              @click="toggleBank(b.key)"
              role="listitem"
            >
              <div class="bank-card__logoWrap">
                <img
                  class="bank-card__logo bank-card__logo--circle"
                  :src="logoByKey(b.key)"
                  :alt="b.label"
                  loading="lazy"
                />
              </div>
              <div class="bank-card__name">{{ b.label }}</div>
              <span class="bank-card__plus" aria-hidden="true">+</span>
            </button>
          </div>

          <button
            class="bank-nav bank-nav--right"
            type="button"
            :disabled="(bankPage + 1) * BANKS_PER_PAGE >= BANKS.length"
            @click="bankNext"
            aria-label="다음 은행"
          >
            ›
          </button>
        </div>

        <!-- 선택된 은행 칩 -->
        <div v-if="selectedBanks.length" class="bank-chips" aria-label="선택된 은행">
          <div class="bank-chip" v-for="b in selectedBanks" :key="b.key">
            <img class="bank-chip__logo" :src="logoByKey(b.key)" :alt="b.label" />
            <span class="bank-chip__text">{{ b.label }}</span>
            <button class="bank-chip__x" type="button" @click="removeBank(b.key)" aria-label="은행 선택 해제">
              ×
            </button>
          </div>
          <button class="bank-clear" type="button" @click="clearBanks">
            전체 해제
          </button>
        </div>
      </div>

      <!-- 로딩/에러 -->
      <div class="fin-state" v-if="loading">
        <div class="spinner" aria-hidden="true"></div>
        <div class="fin-state__text">불러오는 중...</div>
      </div>

      <div v-if="errorMsg" class="fin-error" role="alert">
        {{ errorMsg }}
      </div>

      <!-- 리스트 -->
      <div v-if="!loading" class="list-panel">
        <div class="list-head">
          <div class="list-count">
            <span class="list-count__num">{{ totalCount }}</span>개
          </div>
          <div class="list-sort-hint">
            최고금리 기준 표시
          </div>
        </div>

        <div v-if="pagedItems.length === 0" class="list-empty">
          데이터가 없습니다.
        </div>

        <div v-else class="list">
          <article
            v-for="item in pagedItems"
            :key="item.fin_prdt_cd + '-' + item._rowKey"
            class="list-item"
          >
            <div class="list-item__left">
              <div class="list-item__logo">
                <img :src="logoByApiName(item.kor_co_nm)" :alt="item.kor_co_nm" />
              </div>

              <div class="list-item__meta">
                <RouterLink
                  class="list-item__title"
                  :to="detailLink(item)"
                >
                  {{ item.fin_prdt_nm }}
                </RouterLink>

                <div class="list-item__sub">
                  <span class="list-item__bank">{{ displayBankName(item.kor_co_nm) }}</span>
                  <span class="dot">·</span>
                  <span class="list-item__term">가입기간 {{ item.save_trm }}개월</span>
                </div>
              </div>
            </div>

            <div class="list-item__right">
              <div class="rate">
                <div class="rate__label">최고</div>
                <div class="rate__value">{{ fmtRate(item.intr_rate) }}%</div>
              </div>
              <div class="list-item__actions">
                <button
                  class="btn-bookmark"
                  :class="{ bookmarked: isBookmarked(item.fin_prdt_cd) }"
                  @click="toggleBookmark(item.fin_prdt_cd)"
                  :title="isBookmarked(item.fin_prdt_cd) ? '관심상품 해제' : '관심상품 등록'"
                >
                  {{ isBookmarked(item.fin_prdt_cd) ? '❤️' : '🤍' }}
                </button>
                <RouterLink
                  class="btn-detail"
                  :to="detailLink(item)"
                >
                  자세히 →
                </RouterLink>
              </div>
            </div>
          </article>
        </div>

        <!-- 페이지네이션 (10개/페이지) -->
        <nav v-if="totalPages > 1" class="pager" aria-label="페이지 이동">
          <button class="pager-btn" type="button" :disabled="page === 1" @click="goPage(page - 1)">
            이전
          </button>

          <button
            v-for="p in pageNumbers"
            :key="p"
            class="pager-num"
            :class="{ active: p === page }"
            type="button"
            @click="goPage(p)"
          >
            {{ p }}
          </button>

          <button class="pager-btn" type="button" :disabled="page === totalPages" @click="goPage(page + 1)">
            다음
          </button>
        </nav>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue"
import { useRouter, useRoute } from "vue-router"
import {
  // 예금
  getDeposits,
  syncDeposits as apiSyncDeposits,
  // 적금
  getSavings,
  syncSavings,
} from "@/api/finances"
import api from "@/api/axios"

// ----------------------------
// 고정 은행 테이블 (표시명/로고 제어)
// ----------------------------
const BANKS = [
  { key: "knbank", apiName: "경남은행", label: "경남", logo: "knbank.png" },
  { key: "kjbank", apiName: "광주은행", label: "광주", logo: "kjbank.png" },
  { key: "kb", apiName: "국민은행", label: "KB국민", logo: "kb.png" },
  { key: "nh", apiName: "농협은행주식회사", label: "NH농협", logo: "nh.png" },
  { key: "bnk", apiName: "부산은행", label: "부산", logo: "bnk.png" },
  { key: "sh", apiName: "수협은행", label: "수협", logo: "sh.png" },
  { key: "shinhan", apiName: "신한은행", label: "신한", logo: "shinhan.png" },
  { key: "imbank", apiName: "아이엠뱅크", label: "iM뱅크", logo: "imbank.png" },
  { key: "woori", apiName: "우리은행", label: "우리", logo: "woori.png" },
  { key: "jb", apiName: "전북은행", label: "전북", logo: "jb.png" },
  { key: "jj", apiName: "제주은행", label: "제주", logo: "jj.png" },
  { key: "kakao", apiName: "주식회사 카카오뱅크", label: "카카오뱅크", logo: "kakao.png" },
  { key: "kbank", apiName: "주식회사 케이뱅크", label: "케이뱅크", logo: "kbank.png" },
  { key: "hana", apiName: "주식회사 하나은행", label: "하나", logo: "hana.png" },
  { key: "ibk", apiName: "중소기업은행", label: "IBK기업", logo: "ibk.png" },
  { key: "toss", apiName: "토스뱅크 주식회사", label: "토스뱅크", logo: "toss.png" },
  { key: "kdb", apiName: "한국산업은행", label: "KDB산업", logo: "kdb.png" },
  { key: "sc", apiName: "한국스탠다드차타드은행", label: "SC제일", logo: "sc.png" },
]

// 빠른 매핑
const byKey = new Map(BANKS.map(b => [b.key, b]))
const byApiName = new Map(BANKS.map(b => [b.apiName, b]))

// 로고 경로: 너 프로젝트에 맞게 여기만 조정하면 됨.
const logoByKey = (key) => {
  const b = byKey.get(key)
  // 예) src/assets/banks/*.png 로 두는 경우
  return new URL(`../../assets/banks/${b?.logo ?? "default.png"}`, import.meta.url).href
}

const logoByApiName = (apiName) => {
  const b = byApiName.get(apiName)
  return b ? logoByKey(b.key) : new URL(`../../assets/banks/default.png`, import.meta.url).href
}

const displayBankName = (apiName) => byApiName.get(apiName)?.label ?? apiName

// ----------------------------
// 상태
// ----------------------------
const router = useRouter()
const route = useRoute()

// Alert composable
import AlertModal from "@/components/common/AlertModal.vue"
import { useAlert } from "@/composables/useAlert"
const { showAlert, alertConfig, error } = useAlert()

const activeTab = ref("deposit") // 'deposit' | 'saving'
const loading = ref(false)
const errorMsg = ref("")

// 은행 선택 (멀티)
const selectedBankKeys = ref([]) // ['kb','shinhan',...]
const selectedBankKeysSet = computed(() => new Set(selectedBankKeys.value))
const selectedBanks = computed(() => selectedBankKeys.value.map(k => byKey.get(k)).filter(Boolean))

// 은행 슬라이드(8개/페이지)
const BANKS_PER_PAGE = 9
const bankPage = ref(0)
const visibleBanks = computed(() => {
  const start = bankPage.value * BANKS_PER_PAGE
  return BANKS.slice(start, start + BANKS_PER_PAGE)
})

// 리스트 데이터(통합)
const allItems = ref([]) // 현재 탭 기준 raw list
const page = ref(1)
const PAGE_SIZE = 10

// 북마크 상태
const bookmarkedProducts = ref(new Set())

// ----------------------------
// 데이터 로드/동기화: "비어있으면 동기화" 전략
// ----------------------------
const ensureDepositReady = async () => {
  const list = await getDeposits("") // 전체
  if (Array.isArray(list) && list.length > 0) return
  await apiSyncDeposits()
}

const ensureSavingReady = async () => {
  const res = await getSavings("")
  const items = res?.data ?? []
  console.log(JSON.stringify(allItems.value?.[0], null, 2))
  if (Array.isArray(items) && items.length > 0) return
  await syncSavings()
}

const fetchList = async () => {
  loading.value = true
  errorMsg.value = ""
  try {
    if (activeTab.value === "deposit") {
      await ensureDepositReady()
      const list = await getDeposits("") // 전체 가져오고 프론트에서 필터
      allItems.value = normalizeDeposit(list)
    } else {
      await ensureSavingReady()
      const res = await getSavings("")
      allItems.value = normalizeSaving(res?.data ?? [])
    }
  } catch (e) {
    errorMsg.value = e?.message ? `데이터 로드 실패: ${e.message}` : "데이터 로드에 실패했습니다."
    allItems.value = []
  } finally {
    loading.value = false
  }
}

// API 응답 정규화(최고금리/가입기간 필드 보정)
const normalizeDeposit = (arr) => {
  // deposit은 이미 item에 intr_rate, save_trm이 포함된다고 했으므로 그대로 사용
  // 혹시 같은 상품이 옵션이 여러 개면 “최고금리 기준 1개”로 압축하는 로직을 넣을 수 있음.
  return (arr ?? []).map((x, i) => ({
    ...x,
    intr_rate: Number(x.intr_rate ?? 0),
    save_trm: Number(x.save_trm ?? 0),
    _rowKey: i,
  }))
}

const normalizeSaving = (arr) => {
  return (arr ?? []).map((x, i) => ({
    ...x,
    intr_rate: Number(x.intr_rate ?? 0),
    save_trm: Number(x.save_trm ?? 0),
    _rowKey: i,
  }))
}

// ----------------------------
// 필터링(선택 은행들만)
// ----------------------------
const filteredItems = computed(() => {
  const keys = selectedBankKeys.value
  if (!keys.length) return sortedItems.value

  const apiNames = keys.map(k => byKey.get(k)?.apiName).filter(Boolean)
  return sortedItems.value.filter(it => apiNames.includes(it.kor_co_nm))
})

// 정렬: 최고금리 desc
const sortedItems = computed(() => {
  const copy = [...allItems.value]
  copy.sort((a, b) => (Number(b.intr_rate) || 0) - (Number(a.intr_rate) || 0))
  return copy
})

// ----------------------------
// 페이지네이션
// ----------------------------
const totalCount = computed(() => filteredItems.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / PAGE_SIZE)))

const pagedItems = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filteredItems.value.slice(start, start + PAGE_SIZE)
})

const pageNumbers = computed(() => {
  // 단순 전체 표시(상품 많으면 windowing로 바꿀 수 있음)
  return Array.from({ length: totalPages.value }, (_, i) => i + 1)
})

const goPage = (p) => {
  const next = Math.min(Math.max(1, p), totalPages.value)
  page.value = next
  // 리스트 이동시 상단으로(원하면)
  window.scrollTo({ top: 0, behavior: "smooth" })
}

// 필터/탭 바뀌면 page=1로
watch([activeTab, selectedBankKeys], () => {
  page.value = 1
})

// ----------------------------
// UI 핸들러
// ----------------------------
const setTab = async (tab) => {
  if (activeTab.value === tab) return
  activeTab.value = tab
  await fetchList()
}

const toggleBank = (key) => {
  const set = new Set(selectedBankKeys.value)
  if (set.has(key)) set.delete(key)
  else set.add(key)
  selectedBankKeys.value = Array.from(set)
}

const removeBank = (key) => {
  selectedBankKeys.value = selectedBankKeys.value.filter(k => k !== key)
}

const clearBanks = () => {
  selectedBankKeys.value = []
}

const bankPrev = () => {
  bankPage.value = Math.max(0, bankPage.value - 1)
}

const bankNext = () => {
  const maxPage = Math.floor((BANKS.length - 1) / BANKS_PER_PAGE)
  bankPage.value = Math.min(maxPage, bankPage.value + 1)
}

const goGoldSilver = () => {
  router.push({ name: "gold_silver" })
}

// 상세 라우팅
const detailLink = (item) => {
  if (activeTab.value === "deposit") {
    return { name: "deposit_detail", params: { fin_prdt_cd: item.fin_prdt_cd } }
  }
  return { name: "saving_detail", params: { fin_prdt_cd: item.fin_prdt_cd } }
}

const fmtRate = (v) => {
  const n = Number(v)
  if (Number.isNaN(n)) return "0.00"
  return n.toFixed(2)
}

// ----------------------------
// 북마크 기능
// ----------------------------
const fetchBookmarks = async () => {
  try {
    const res = await api.get("/accounts/bookmarks/")
    bookmarkedProducts.value = new Set(res.data.map(b => b.fin_prdt_cd))
  } catch (error) {
    console.error("북마크 로딩 실패:", error)
  }
}

const toggleBookmark = async (finPrdtCd) => {
  try {
    await api.post(`/accounts/recommendations/${finPrdtCd}/bookmark/`)

    // 북마크 상태 토글
    if (bookmarkedProducts.value.has(finPrdtCd)) {
      bookmarkedProducts.value.delete(finPrdtCd)
    } else {
      bookmarkedProducts.value.add(finPrdtCd)
    }
  } catch (err) {
    console.error("북마크 실패:", err)
    error("북마크에 실패했습니다.")
  }
}

const isBookmarked = (finPrdtCd) => {
  return bookmarkedProducts.value.has(finPrdtCd)
}

// ----------------------------
// 마운트: fin_home 들어오면 예금 자동 준비 + 리스트 표시
// ----------------------------
onMounted(async () => {
  // Query parameter로 tab이 전달되면 해당 탭으로 설정
  const tabFromQuery = route.query.tab
  if (tabFromQuery === "saving") {
    activeTab.value = "saving"
  } else {
    activeTab.value = "deposit"
  }

  await fetchList()
  await fetchBookmarks()
})
</script>

<style scoped>
/* 전체 배경/중앙 */
.fin-page {
  padding: 18px 12px 40px;
  background: #f5f7fb;
  min-height: calc(100vh - 60px);
}
.fin-shell {
  max-width: 980px;
  margin: 0 auto;
}

/* 상단 안내(선택) */
.fin-notice {
  text-align: center;
  background: #ffffff;
  border-radius: 14px;
  padding: 14px 16px;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
  margin-bottom: 12px;
}
.fin-notice__hl {
  color: #3182F6;
  font-weight: 900;
}
.fin-notice__text {
  display: inline-block;
  color: rgba(15, 23, 42, 0.70);
  font-weight: 700;
}
.fin-tabs-wrap {
  display: flex;
  justify-content: center;
}

/* 탭 */
.fin-tabs {
  display: inline-flex;
  gap: 6px;
  padding: 6px;
  border-radius: 999px;
  background: #fff;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
  margin: 10px auto 14px;
}
.fin-tab {
  border: 0;
  background: transparent;
  padding: 10px 16px;
  border-radius: 999px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.55);
  cursor: pointer;
}
.fin-tab.active {
  background: #eef4ff;
  color: #111827;
}

/* 은행 패널 */
.bank-panel {
  background: #fff;
  border-radius: 16px;
  padding: 14px 12px 12px;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
  margin-bottom: 14px;
}
.bank-panel__inner {
  display: grid;
  grid-template-columns: 40px 1fr 40px;
  gap: 10px;
  align-items: center;
}

/* 좌/우 버튼 */
.bank-nav {
  width: 36px;
  height: 56px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.10);
  background: #fff;
  font-size: 22px;
  font-weight: 900;
  cursor: pointer;
}
.bank-nav:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 은행 1줄 (8개/페이지: visibleBanks로 제한) */
.bank-row {
  display: flex;
  align-items: stretch;
  gap: 10px;
  overflow: hidden;
  padding: 2px;
}

/* 은행 카드 (작게) */
.bank-card {
  border: 1px solid rgba(15, 23, 42, 0.10);
  background: #fff;
  cursor: pointer;
  transition: box-shadow 160ms ease, transform 160ms ease, border-color 160ms ease;
}
.bank-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 18px 34px rgba(15, 23, 42, 0.08);
}
.bank-card--mini {
  position: relative;
  width: 86px;
  min-width: 86px;
  height: 92px;
  padding: 10px 8px 8px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  gap: 8px;
}
.bank-card__logoWrap {
  width: 38px;
  height: 38px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.10);
  display: grid;
  place-items: center;
  overflow: hidden;
}
.bank-card__logo {
  display: block;
}
.bank-card__logo--circle {
  width: 100%;
  height: 100%;
  border-radius: 999px;
  object-fit: cover;   /* contain -> cover */
  display: block;
}
.bank-card__name {
  font-size: 12px;
  font-weight: 900;
  line-height: 1;
  color: rgba(15, 23, 42, 0.92);
}
.bank-card__plus {
  position: absolute;
  top: 6px;
  right: 7px;
  font-weight: 900;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.35);
}
.bank-card.selected {
  border-color: rgba(37, 99, 235, 0.55);
  box-shadow: 0 18px 34px rgba(37, 99, 235, 0.12);
}

/* 선택 칩 */
.bank-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}
.bank-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 999px;
  background: #f3f6ff;
  border: 1px solid rgba(37, 99, 235, 0.14);
}
.bank-chip__logo {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  object-fit: contain;
}
.bank-chip__text {
  font-weight: 900;
  color: rgba(15, 23, 42, 0.78);
  font-size: 12px;
}
.bank-chip__x {
  border: 0;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.08);
  color: rgba(15, 23, 42, 0.65);
  font-weight: 900;
  cursor: pointer;
}
.bank-clear {
  border: 0;
  background: transparent;
  color: rgba(37, 99, 235, 0.95);
  font-weight: 900;
  cursor: pointer;
  padding: 6px 8px;
}

/* 로딩/에러 */
.fin-state {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 6px;
  color: rgba(15, 23, 42, 0.70);
  font-weight: 800;
}
.spinner {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  border: 3px solid rgba(37, 99, 235, 0.20);
  border-top-color: rgba(37, 99, 235, 0.95);
  animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.fin-error {
  background: #fff1f2;
  border: 1px solid rgba(225, 29, 72, 0.20);
  color: rgba(159, 18, 57, 0.95);
  border-radius: 14px;
  padding: 12px 14px;
  font-weight: 900;
  margin-bottom: 12px;
}

/* 리스트 패널 */
.list-panel {
  background: #fff;
  border-radius: 16px;
  padding: 14px 14px 16px;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
}
.list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 2px 12px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
  margin-bottom: 10px;
}
.list-count {
  font-weight: 900;
  color: rgba(15, 23, 42, 0.70);
}
.list-count__num {
  color: #16a34a;
  font-size: 20px;
  margin-right: 4px;
}
.list-sort-hint {
  color: rgba(15, 23, 42, 0.45);
  font-weight: 800;
  font-size: 12px;
}
.list-empty {
  padding: 28px 10px;
  text-align: center;
  color: rgba(15, 23, 42, 0.55);
  font-weight: 900;
}

/* 아이템 */
.list {
  display: grid;
  gap: 10px;
}
.list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 12px;
  border-radius: 14px;
  border: 1px solid rgba(15, 23, 42, 0.08);
}
.list-item__left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.list-item__logo {
  width: 44px;
  height: 44px;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.10);
  background: #fff;
  display: grid;
  place-items: center;
  overflow: hidden;
}
.list-item__logo img {
  width: 100%;
  height: 100%;
  border-radius: 999px;
  object-fit: cover;   /* contain -> cover */
  display: block;
}
.list-item__meta {
  min-width: 0;
}
.list-item__title {
  display: inline-block;
  font-weight: 950;
  color: rgba(15, 23, 42, 0.92);
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 520px;
}
.list-item__title:hover {
  text-decoration: underline;
}
.list-item__sub {
  margin-top: 4px;
  display: flex;
  gap: 6px;
  align-items: center;
  color: rgba(15, 23, 42, 0.58);
  font-weight: 800;
  font-size: 12px;
}
.dot { opacity: 0.55; }

/* 우측 금리 */
.list-item__right {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}
.rate {
  text-align: right;
  min-width: 96px;
}
.rate__label {
  font-size: 12px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.45);
}
.rate__value {
  font-size: 18px;
  font-weight: 950;
  color: #16a34a;
}

/* 액션 버튼들 */
.list-item__actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

.btn-bookmark {
  border: 0;
  background: transparent;
  cursor: pointer;
  font-size: 20px;
  padding: 4px;
  line-height: 1;
  transition: transform 0.2s ease;
}
.btn-bookmark:hover {
  transform: scale(1.15);
}

.btn-detail {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 8px;
  background: linear-gradient(135deg, #3182F6, #2563eb);
  color: #fff;
  font-size: 13px;
  font-weight: 900;
  text-decoration: none;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
}
.btn-detail:hover {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
  transform: translateY(-1px);
}

/* 페이지네이션 */
.pager {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 16px;
}
.pager-btn,
.pager-num {
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: #fff;
  border-radius: 12px;
  padding: 10px 12px;
  font-weight: 900;
  cursor: pointer;
  color: rgba(15, 23, 42, 0.72);
}
.pager-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.pager-num.active {
  border-color: rgba(37, 99, 235, 0.65);
  background: #eef4ff;
  color: rgba(15, 23, 42, 0.92);
}

/* 반응형 */
@media (max-width: 720px) {
  .list-item__title { max-width: 320px; }
}
@media (max-width: 520px) {
  .bank-card--mini { width: 78px; min-width: 78px; height: 88px; }
  .list-item__title { max-width: 210px; }
}
</style>
