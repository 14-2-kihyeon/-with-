<template>
  <div class="stocks-search-section">
    <header class="section-header">
      <h1 class="title">{{ marketName }} 검색</h1>
      <p class="sub">{{ searchPlaceholder }}</p>
    </header>

    <div class="card">
      <div class="search-row">
        <input
          v-model="searchQuery"
          class="search-input"
          :placeholder="searchPlaceholder"
          @keyup.enter="handleSearch"
        />
        <button class="btn" @click="handleSearch">검색</button>
      </div>

      <div v-if="error" class="error">{{ error }}</div>

      <ul v-if="results.length" class="result-list">
        <li v-for="item in results" :key="item.code" class="result-item">
          <div class="left">
            <div class="name">{{ item.name }}</div>
            <div class="meta">{{ item.code }} <span v-if="item.market">· {{ item.market }}</span></div>
          </div>

          <RouterLink class="link" :to="{ name: 'stock_detail', params: { code: item.code } }">
            상세보기 →
          </RouterLink>
        </li>
      </ul>

      <div v-else class="empty">
        {{ emptyMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  marketName: {
    type: String,
    required: true
  },
  searchPlaceholder: {
    type: String,
    default: '종목명 또는 코드를 입력하세요'
  },
  emptyMessage: {
    type: String,
    default: '검색 결과가 없습니다.'
  },
  onSearch: {
    type: Function,
    required: true
  }
})

const searchQuery = ref('')
const results = ref([])
const error = ref(null)

const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    error.value = '검색어를 입력해주세요'
    return
  }

  error.value = null
  results.value = []

  try {
    const data = await props.onSearch(searchQuery.value)
    results.value = data || []
  } catch (e) {
    error.value = e.message || '검색 중 오류가 발생했습니다'
  }
}
</script>

<style scoped>
.section-header { margin-bottom: 14px; }
.title { font-size: 28px; font-weight: 800; }
.sub { opacity: 0.7; margin-top: 6px; }

.card { background: rgba(255,255,255,0.85); border-radius: 14px; padding: 16px; margin-bottom: 14px; }
.search-row { display: flex; gap: 10px; align-items: center; }
.search-input { flex: 1; padding: 12px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.12); }
.btn { padding: 12px 14px; border-radius: 10px; border: none; cursor: pointer; background: #2563eb; color: white; font-weight: 700; }
.error { margin-top: 10px; color: #b00020; }

.result-list { list-style: none; padding: 0; margin: 12px 0 0; }
.result-item { display: flex; justify-content: space-between; align-items: center; padding: 12px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.08); margin-bottom: 10px; }
.name { font-weight: 800; }
.meta { opacity: 0.7; font-size: 13px; margin-top: 4px; }
.link { text-decoration: none; font-weight: 800; color: #2563eb; }
.empty { margin-top: 10px; opacity: 0.75; }
</style>
