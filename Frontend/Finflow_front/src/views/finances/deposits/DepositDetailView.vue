<template>
  <div class="page">
    <!-- Top bar -->
    <div class="topbar">
      <button class="back-btn" type="button" @click="goBackToFinHome">
        ← 목록으로
      </button>

      <div class="topbar-title">
        <div class="kicker">정기예금</div>
        <div class="title">상품 상세</div>
      </div>
      <div class="topbar-spacer" />
    </div>

    <p v-if="errorMsg" class="err">{{ errorMsg }}</p>

    <!-- skeleton / loading -->
    <div v-if="loading" class="card card--skeleton">
      <div class="skeleton-line w-60" />
      <div class="skeleton-line w-40" />
      <div class="skeleton-block" />
      <div class="skeleton-line w-70" />
      <div class="skeleton-line w-55" />
    </div>

    <div v-else-if="product" class="content">
      <!-- 헤더 카드 -->
      <section class="card header-card">
        <div class="bank">
          <div class="bank-logo">
            <img
              v-if="bankMeta?.logoSrc"
              :src="bankMeta.logoSrc"
              :alt="bankMeta.label"
              class="bank-logo-img"
            />
            <div v-else class="bank-logo-fallback">
              {{ bankMeta?.label?.[0] ?? "B" }}
            </div>
          </div>

          <div class="bank-info">
            <div class="bank-name">{{ bankMeta?.label ?? product.kor_co_nm }}</div>
            <div class="product-name">{{ product.fin_prdt_nm }}</div>
            <div class="code mono">상품코드 · {{ product.fin_prdt_cd }}</div>
          </div>

          <div class="rate-summary">
            <div class="rate-pill">
              <div class="rate-label">최고금리</div>
              <div class="rate-value">
                {{ bestRateText }}
              </div>
            </div>
            <div class="term-pill">
              <div class="term-label">대표 만기</div>
              <div class="term-value">
                {{ bestTermText }}
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 상품 정보 카드 -->
      <section class="card">
        <div class="section-title">상품 정보</div>

        <div class="info-grid">
          <div class="info-item">
            <div class="info-k">가입방법</div>
            <div class="info-v">{{ product.join_way || "-" }}</div>
          </div>

          <div class="info-item">
            <div class="info-k">가입대상</div>
            <div class="info-v">{{ product.join_member || "-" }}</div>
          </div>

          <div class="info-item info-item--full">
            <div class="info-k">우대조건</div>
            <div class="info-v info-v--special">
              <div v-if="product.spcl_cnd" class="special-conditions">
                <div v-for="(condition, idx) in formatSpecialConditions(product.spcl_cnd)" :key="idx" class="condition-item">
                  <span class="condition-bullet">•</span>
                  <span class="condition-text">{{ condition }}</span>
                </div>
              </div>
              <span v-else>-</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 금리 옵션 카드 -->
      <section class="card">
        <div class="section-head">
          <div class="section-title">금리 옵션</div>
          <div class="hint">기간별 기본/최고 금리를 확인하세요</div>
        </div>

        <div v-if="optionsSorted.length === 0" class="empty">
          옵션이 없습니다.
        </div>

        <div v-else class="options-table-wrap">
          <table class="options-table">
            <thead>
              <tr>
                <th class="th-center" style="width: 110px;">기간</th>
                <th class="th-right" style="width: 120px;">기본금리</th>
                <th class="th-right" style="width: 120px;">최고금리</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(o, idx) in optionsSorted" :key="idx">
                <td class="td-center">
                  <span class="term-chip">{{ o.save_trm }}개월</span>
                </td>
                <td class="td-right">
                  {{ formatRate(o.intr_rate) }}
                </td>
                <td class="td-right">
                  <span class="best">
                    {{ formatRate(o.intr_rate2) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- bottom actions -->
      <div class="bottom-actions">
        <button class="primary-btn" type="button" @click="goBackToFinHome">
          예금 리스트로 돌아가기
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { getDepositDetail } from "@/api/finances"

/**
 * ✅ 임시(권장: constants로 분리)
 * FinHomeView에서 쓰는 BANKS와 동일한 매핑을 여기에도 둡니다.
 * 로고 경로는 예시로: /src/assets/banks/{logo} 를 가정
 * 프로젝트 구조에 맞게 아래 logoSrc 생성만 조정하면 됩니다.
 */
const BANKS = [
  { key: "knbank", apiName: "경남은행", label: "경남", logo: "knbank.png" },
  { key: "kjbank", apiName: "광주은행", label: "광주", logo: "kjbank.png" },
  { key: "kb",     apiName: "국민은행", label: "KB국민", logo: "kb.png" },
  { key: "nh",     apiName: "농협은행주식회사", label: "NH농협", logo: "nh.png" },
  { key: "bnk",    apiName: "부산은행", label: "부산", logo: "bnk.png" },
  { key: "sh",     apiName: "수협은행", label: "수협", logo: "sh.png" },
  { key: "shinhan",apiName: "신한은행", label: "신한", logo: "shinhan.png" },
  { key: "imbank", apiName: "아이엠뱅크", label: "iM뱅크", logo: "imbank.png" },
  { key: "woori",  apiName: "우리은행", label: "우리", logo: "woori.png" },
  { key: "jb",     apiName: "전북은행", label: "전북", logo: "jb.png" },
  { key: "jj",     apiName: "제주은행", label: "제주", logo: "jj.png" },
  { key: "kakao",  apiName: "주식회사 카카오뱅크", label: "카카오뱅크", logo: "kakao.png" },
  { key: "kbank",  apiName: "주식회사 케이뱅크", label: "케이뱅크", logo: "kbank.png" },
  { key: "hana",   apiName: "주식회사 하나은행", label: "하나", logo: "hana.png" },
  { key: "ibk",    apiName: "중소기업은행", label: "IBK기업", logo: "ibk.png" },
  { key: "toss",   apiName: "토스뱅크 주식회사", label: "토스뱅크", logo: "toss.png" },
  { key: "kdb",    apiName: "한국산업은행", label: "KDB산업", logo: "kdb.png" },
  { key: "sc",     apiName: "한국스탠다드차타드은행", label: "SC제일", logo: "sc.png" },
]

const route = useRoute()
const router = useRouter()

const product = ref(null)
const loading = ref(false)
const errorMsg = ref("")

const formatRate = (v) => {
  if (v === null || v === undefined) return "-"
  if (Number(v) < 0) return "정보없음"
  // intr_rate가 문자열로 올 수도 있으니 Number로 방어
  const n = Number(v)
  if (Number.isNaN(n)) return "-"
  return `${n.toFixed(2).replace(/\.00$/, "")}%`
}

const formatSpecialConditions = (text) => {
  if (!text) return []

  // 1. 명확한 번호로 시작하는 항목만 분리 (예: "1.", "2.", "①", "②" 등)
  let conditions = text.split(/(?=\d+\.\s|[①②③④⑤⑥⑦⑧⑨⑩]\s)/)

  // 분리된 항목이 2개 이상이면 (즉, 순번이 있으면) 그대로 반환
  if (conditions.length > 1) {
    return conditions
      .map(c => c.trim())
      .filter(c => c.length > 0)
      .map(c => c.replace(/^[•\-\*]\s*/, ''))
  }

  // 2. 순번이 없고, 세미콜론이 있으면 세미콜론으로 분리
  if (text.includes(';')) {
    conditions = text.split(/;\s*/)
  }

  // 3. 여전히 분리되지 않았고, "단," "※" 등으로 시작하는 특별한 경우만 분리
  if (conditions.length === 1 && /(?:단,|※|＊|★)/.test(text)) {
    conditions = text.split(/(?=단,|※|＊|★)/)
  }

  // 빈 문자열 제거 및 트림
  return conditions
    .map(c => c.trim())
    .filter(c => c.length > 0)
    .map(c => c.replace(/^[•\-\*]\s*/, ''))
}

const bankMeta = computed(() => {
  if (!product.value) return null
  const found = BANKS.find(b => b.apiName === product.value.kor_co_nm)
  if (!found) return { label: product.value.kor_co_nm, logoSrc: "" }

  // ✅ 로고 위치: src/assets/banks/ 아래로 가정
  // 실제 폴더에 맞춰 경로만 수정하면 됨
  const logoSrc = new URL(`../../../assets/banks/${found.logo}`, import.meta.url).href
  return { ...found, logoSrc }
})

const optionsSorted = computed(() => {
  const opts = product.value?.options ?? []
  return [...opts].sort((a, b) => Number(a.save_trm ?? 0) - Number(b.save_trm ?? 0))
})

const bestOption = computed(() => {
  const opts = product.value?.options ?? []
  if (!opts.length) return null
  const rateOf = (o) => {
    const r2 = o.intr_rate2
    const r1 = o.intr_rate
    const v = r2 ?? r1 ?? 0
    return Number(v) || 0
  }
  return opts.reduce((best, cur) => (rateOf(cur) > rateOf(best) ? cur : best), opts[0])
})

const bestRateText = computed(() => {
  const o = bestOption.value
  if (!o) return "-"
  return formatRate(o.intr_rate2 ?? o.intr_rate)
})

const bestTermText = computed(() => {
  const o = bestOption.value
  if (!o) return "-"
  const t = Number(o.save_trm ?? 0)
  return t ? `${t}개월` : "-"
})

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

const goBackToFinHome = () => {
  router.push({ name: "fin_home" })
}

onMounted(loadDetail)
watch(() => route.params.fin_prdt_cd, loadDetail)
</script>

<style scoped>
.page {
  padding: 16px;
  max-width: 980px;
  margin: 0 auto;
}

/* Topbar */
.topbar {
  display: grid;
  grid-template-columns: 120px 1fr 120px;
  align-items: center;
  gap: 10px;
  margin: 8px 0 14px;
}

.back-btn {
  justify-self: start;
  border: 0;
  background: transparent;
  color: rgba(37, 99, 235, 0.95); /* Toss 느낌의 blue 계열 */
  font-weight: 800;
  cursor: pointer;
  padding: 8px 8px;
  border-radius: 10px;
}

.back-btn:hover {
  background: rgba(37, 99, 235, 0.08);
}

.topbar-title {
  text-align: center;
}
.kicker {
  font-size: 12px;
  font-weight: 800;
  color: rgba(15, 23, 42, 0.55);
}
.title {
  font-size: 18px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.95);
}
.topbar-spacer {}

/* Card */
.card {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
  border-radius: 16px;
  padding: 18px;
  margin-bottom: 14px;
}

.header-card {
  padding: 18px;
}

.bank {
  display: grid;
  grid-template-columns: 64px 1fr auto;
  gap: 14px;
  align-items: center;
}

.bank-logo {
  width: 56px;
  height: 56px;
  border-radius: 999px;
  overflow: hidden;
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.10);
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.08);
  display: grid;
  place-items: center;
}

.bank-logo-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.bank-logo-fallback {
  font-weight: 900;
  color: rgba(15, 23, 42, 0.75);
}

.bank-name {
  font-size: 14px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.78);
}

.product-name {
  font-size: 18px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.96);
  margin-top: 2px;
  line-height: 1.2;
}

.code {
  font-size: 12px;
  color: rgba(15, 23, 42, 0.52);
  margin-top: 6px;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
}

.rate-summary {
  display: grid;
  gap: 8px;
  justify-items: end;
}

.rate-pill, .term-pill {
  min-width: 118px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(37, 99, 235, 0.06);
  border: 1px solid rgba(37, 99, 235, 0.14);
  text-align: right;
}

.rate-label, .term-label {
  font-size: 11px;
  font-weight: 900;
  color: rgba(37, 99, 235, 0.70);
}

.rate-value, .term-value {
  font-size: 16px;
  font-weight: 900;
  color: rgba(37, 99, 235, 0.95);
  margin-top: 2px;
}

/* Section */
.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.section-title {
  font-size: 15px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.95);
}

.hint {
  font-size: 12px;
  color: rgba(15, 23, 42, 0.55);
}

/* Info grid */
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.info-item {
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.65);
}

.info-item--full {
  grid-column: 1 / -1;
}

.info-k {
  font-size: 12px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.60);
  margin-bottom: 6px;
}

.info-v {
  font-size: 13px;
  color: rgba(15, 23, 42, 0.86);
  line-height: 1.5;
}

.info-v--special {
  line-height: 1.7;
}

.special-conditions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.condition-item {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.condition-bullet {
  color: rgba(37, 99, 235, 0.75);
  font-weight: 900;
  flex-shrink: 0;
  line-height: 1.5;
}

.condition-text {
  flex: 1;
  color: rgba(15, 23, 42, 0.86);
  line-height: 1.6;
  word-break: keep-all;
}

/* Options table */
.options-table-wrap {
  overflow-x: auto;
  border-radius: 14px;
  border: 1px solid rgba(15, 23, 42, 0.08);
}

.options-table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(255, 255, 255, 0.72);
}

.options-table th {
  padding: 12px 12px;
  font-size: 12px;
  font-weight: 900;
  color: rgba(15, 23, 42, 0.70);
  background: rgba(15, 23, 42, 0.03);
}

.options-table td {
  padding: 12px 12px;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
  font-size: 13px;
  color: rgba(15, 23, 42, 0.85);
}

.th-center { text-align: center; }
.th-right { text-align: right; }
.td-center { text-align: center; }
.td-right { text-align: right; }
.td-muted { color: rgba(15, 23, 42, 0.60); }

.term-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  border: 1px solid rgba(15, 23, 42, 0.08);
  font-weight: 900;
  font-size: 12px;
}

.best {
  color: rgba(37, 99, 235, 0.95);
  font-weight: 900;
}

.empty {
  padding: 18px;
  text-align: center;
  color: rgba(15, 23, 42, 0.60);
}

/* bottom actions */
.bottom-actions {
  display: flex;
  justify-content: center;
  padding: 6px 0 24px;
}

.primary-btn {
  height: 44px;
  border: 0;
  border-radius: 14px;
  padding: 0 16px;
  background: rgba(37, 99, 235, 0.95);
  color: #fff;
  font-weight: 900;
  cursor: pointer;
  box-shadow: 0 18px 36px rgba(37, 99, 235, 0.22);
}

.primary-btn:hover {
  filter: brightness(0.97);
}

/* error */
.err {
  color: #c00;
  white-space: pre-wrap;
  margin: 10px 0;
}

/* skeleton */
.card--skeleton {
  padding: 18px;
}
.skeleton-line {
  height: 14px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.08);
  margin-bottom: 10px;
}
.skeleton-block {
  height: 140px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.08);
  margin: 12px 0;
}
.w-40 { width: 40%; }
.w-55 { width: 55%; }
.w-60 { width: 60%; }
.w-70 { width: 70%; }

@media (max-width: 720px) {
  .bank {
    grid-template-columns: 56px 1fr;
    grid-template-areas:
      "logo info"
      "rate rate";
  }
  .rate-summary {
    justify-items: start;
    grid-auto-flow: column;
    justify-content: start;
  }
}
</style>
