// 역할: News API 호출 전용 (axios) - 화면 상태 관리 금지


// src/composables/useNaverNews.js
import { ref, computed } from "vue"
import { naverApi } from "@/api/naver"

export function useNaverNews() {
  const query = ref("")
  const mode = ref("all") // all | bookmark

  const rawList = ref([])
  const selectedId = ref(null)
  const selected = ref(null)

  const summary = ref("")
  const loadingList = ref(false)
  const loadingDetail = ref(false)
  const loadingSummary = ref(false)

  const list = computed(() => {
    if (mode.value === "bookmark") {
      return rawList.value.filter(n => n.is_bookmarked)
    }
    return rawList.value
  })

  async function fetchList({ autoSelect = true } = {}) {
    loadingList.value = true
    try {
      rawList.value = await naverApi.list()

      // 북마크 모드인데 결과가 비면 선택 해제
      if (!list.value.length) {
        selectedId.value = null
        selected.value = null
        summary.value = ""
        return
      }

      // 자동 선택
      if (autoSelect) {
        const nextId = selectedId.value ?? list.value[0].id
        await select(nextId)
      }
    } finally {
      loadingList.value = false
    }
  }

  async function runSearch() {
    const q = query.value.trim()
    if (!q) return
    await naverApi.search(q)
    mode.value = "all"
    selectedId.value = null
    await fetchList({ autoSelect: true })
  }

  async function select(id) {
    if (!id) return
    loadingDetail.value = true
    try {
      selectedId.value = id
      selected.value = await naverApi.detail(id)
      summary.value = ""
    } finally {
      loadingDetail.value = false
    }
  }

  async function toggleBookmark(id) {
    if (!id) return
    const updated = await naverApi.toggleBookmark(id)

    // rawList 갱신
    const idx = rawList.value.findIndex(n => n.id === id)
    if (idx !== -1) rawList.value[idx] = updated

    // 북마크 모드에서 해제하면 목록에서 사라짐 → 선택 유지 처리
    if (mode.value === "bookmark" && !updated.is_bookmarked) {
      // 현재 선택이 지워졌으면 다른 거 선택
      if (selectedId.value === id) {
        const next = list.value[0]?.id
        if (next) await select(next)
        else {
          selectedId.value = null
          selected.value = null
          summary.value = ""
        }
      }
    }
  }

  async function summarizeSelected() {
    if (!selectedId.value) return
    loadingSummary.value = true
    summary.value = ""
    try {
      const data = await naverApi.summarize(selectedId.value)
      summary.value = data.summary || "요약 결과가 없습니다."
    } finally {
      loadingSummary.value = false
    }
  }

  function setMode(next) {
    mode.value = next
    // 모드 바뀌면 현재 list 기준으로 선택 보정
    if (list.value.length) {
      const exists = list.value.some(n => n.id === selectedId.value)
      if (!exists) select(list.value[0].id)
    } else {
      selectedId.value = null
      selected.value = null
      summary.value = ""
    }
  }

  return {
    // state
    query,
    mode,
    list,
    selectedId,
    selected,
    summary,
    loadingList,
    loadingDetail,
    loadingSummary,

    // actions
    fetchList,
    runSearch,
    select,
    toggleBookmark,
    summarizeSelected,
    setMode,
  }
}
