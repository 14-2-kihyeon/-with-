// 역할: NaverNewsView 전용 UI 상태/이벤트 로직 - axios 직접 호출 금지(또는 최소화)


// src/composables/useNews.js
import { ref } from "vue";
import { newsApi } from "@/api/news";

export function useNews({ onUnauthorized } = {}) {
  const query = ref("");

  const mode = ref("all"); // "all" | "bookmark"
  const items = ref([]);
  const selectedId = ref(null);
  const detail = ref(null);

  const summary = ref("");
  const loadingList = ref(false);
  const loadingDetail = ref(false);
  const loadingSummary = ref(false);

  function handleAxiosError(err) {
    const status = err?.response?.status;
    if (status === 401 && typeof onUnauthorized === "function") onUnauthorized();
    throw err;
  }

  async function loadList(nextMode = mode.value) {
    loadingList.value = true;
    try {
      const res = await newsApi.list();
      let list = res.data || [];

      if (nextMode === "bookmark") {
        list = list.filter((n) => n.is_bookmarked);
      }

      items.value = list;

      // 자동 선택
      if (list.length > 0) {
        await select(list[0].id);
      } else {
        selectedId.value = null;
        detail.value = null;
        summary.value = "";
      }
    } catch (e) {
      handleAxiosError(e);
    } finally {
      loadingList.value = false;
    }
  }

  async function search() {
    const q = query.value.trim();
    if (!q) return;

    try {
      await newsApi.search(q);
      mode.value = "all";
      await loadList("all");
    } catch (e) {
      handleAxiosError(e);
    }
  }

  async function setMode(nextMode) {
    if (mode.value === nextMode) return;
    mode.value = nextMode;
    summary.value = "";
    await loadList(nextMode);
  }

  async function select(id) {
    selectedId.value = id;
    summary.value = "";
    loadingDetail.value = true;
    try {
      const res = await newsApi.detail(id);
      detail.value = res.data;
    } catch (e) {
      handleAxiosError(e);
    } finally {
      loadingDetail.value = false;
    }
  }

  async function toggleBookmark(id) {
    try {
      const res = await newsApi.toggleBookmark(id);
      const updated = res.data;

      // 목록에서 해당 뉴스 업데이트
      items.value = items.value.map((n) => (n.id === id ? updated : n));

      // 북마크 모드에서 해제되면 목록에서 제거
      if (mode.value === "bookmark" && !updated.is_bookmarked) {
        items.value = items.value.filter((n) => n.id !== id);

        // 선택 항목이 사라졌으면 새로 선택
        if (selectedId.value === id) {
          if (items.value.length > 0) await select(items.value[0].id);
          else {
            selectedId.value = null;
            detail.value = null;
            summary.value = "";
          }
        }
      }
    } catch (e) {
      handleAxiosError(e);
    }
  }

  async function summarizeSelected() {
    if (!selectedId.value) return;
    loadingSummary.value = true;
    summary.value = "";
    try {
      const res = await newsApi.summarize(selectedId.value);
      summary.value = res.data?.summary || "요약 결과가 없습니다.";
    } catch (e) {
      handleAxiosError(e);
    } finally {
      loadingSummary.value = false;
    }
  }

  return {
    query,
    mode,
    items,
    selectedId,
    detail,
    summary,
    loadingList,
    loadingDetail,
    loadingSummary,
    loadList,
    search,
    setMode,
    select,
    toggleBookmark,
    summarizeSelected,
  };
}
