import { defineStore } from "pinia"
import { syncDeposits as apiSyncDeposits, syncSavings as apiSyncSavings } from "@/api/finances"

const KEY = "pb_fin_sync_state_v1"

// TTL: 예) 6시간(원하는 값으로 조절)
const TTL_MS = 6 * 60 * 60 * 1000

function now() {
  return Date.now()
}

function loadState() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "{}")
  } catch {
    return {}
  }
}

function saveState(state) {
  try {
    localStorage.setItem(KEY, JSON.stringify(state))
  } catch {}
}

export const useFinSyncStore = defineStore("finSync", {
  state: () => ({
    syncing: { deposits: false, savings: false },     // 동기화 진행 여부(중복 호출 방지)
    lastSyncedAt: { deposits: 0, savings: 0 },        // 마지막 동기화 시각(ms)
    lastError: { deposits: "", savings: "" },         // 마지막 에러 메시지
  }),

  actions: {
    hydrate() {
      const s = loadState()
      if (s.lastSyncedAt) this.lastSyncedAt = { ...this.lastSyncedAt, ...s.lastSyncedAt }
    },

    _markSynced(kind) {
      this.lastSyncedAt[kind] = now()
      saveState({ lastSyncedAt: this.lastSyncedAt })
    },

    isStale(kind) {
      const t = this.lastSyncedAt[kind] || 0
      return now() - t > TTL_MS
    },

    /**
     * 핵심: 라우팅을 막지 않는 "조건부 동기화"
     * - stale이면 동기화 실행
     * - stale 아니면 아무것도 안 함
     * - syncing 중이면 중복 실행 안 함
     */
    async ensureFresh(kind) {
      this.hydrate()

      if (!this.isStale(kind)) return
      if (this.syncing[kind]) return

      this.syncing[kind] = true
      this.lastError[kind] = ""

      try {
        if (kind === "deposits") {
          await apiSyncDeposits()
        } else if (kind === "savings") {
          await apiSyncSavings()
        } else {
          // 현물/골드는 동기화 정책 필요 시 추가
        }
        this._markSynced(kind)
      } catch (e) {
        this.lastError[kind] = e?.response?.data?.error || e?.message || "sync failed"
      } finally {
        this.syncing[kind] = false
      }
    },

    /** 사용자가 "강제 최신화" 버튼 누를 때 쓰고 싶으면 */
    async forceSync(kind) {
      // stale 여부 무시하고 수행
      this.hydrate()
      if (this.syncing[kind]) return

      this.syncing[kind] = true
      this.lastError[kind] = ""

      try {
        if (kind === "deposits") await apiSyncDeposits()
        else if (kind === "savings") await apiSyncSavings()
        this._markSynced(kind)
      } catch (e) {
        this.lastError[kind] = e?.response?.data?.error || e?.message || "sync failed"
      } finally {
        this.syncing[kind] = false
      }
    },
  },
})
