<template>
  <div class="top-volume-list">
    <div class="card">
      <h2 class="card-title">{{ title }}</h2>
      <div v-if="loading" class="loading">로딩 중...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <ul v-else class="volume-list">
        <li v-for="(item, index) in topItems" :key="item.code" class="volume-item">
          <div class="rank">{{ index + 1 }}</div>
          <div class="info">
            <div class="name">{{ item.name }}</div>
            <div class="code">{{ item.code }}</div>
          </div>
          <div class="volume">
            <div class="amount">{{ formatVolume(item.volume) }}</div>
            <div class="change" :class="item.change >= 0 ? 'positive' : 'negative'">
              {{ formatChange(item.change) }}
            </div>
          </div>
          <RouterLink class="link" :to="{ name: 'stock_detail', params: { code: item.code } }">
            →
          </RouterLink>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiGetRealtimePrice } from '@/api/stocks'

const props = defineProps({
  title: {
    type: String,
    default: '실시간 거래대금 Top 5'
  },
  items: {
    type: Array,
    required: true
  },
  market: {
    type: String,
    default: 'US'
  }
})

const topItems = ref([])
const loading = ref(false)
const error = ref(null)

const formatVolume = (volume) => {
  if (!volume) return '-'
  // 달러 기준 (미국 주식/암호화폐)
  const unit = (props.market === 'US' || props.market === 'CRYPTO') ? '$' : ''

  if (volume >= 1000000000) {
    return unit + (volume / 1000000000).toFixed(1) + 'B'
  } else if (volume >= 1000000) {
    return unit + (volume / 1000000).toFixed(1) + 'M'
  }
  return unit + volume.toLocaleString()
}

const formatChange = (change) => {
  if (!change) return '0%'
  const sign = change >= 0 ? '+' : ''
  return sign + change.toFixed(2) + '%'
}

const fetchTopVolumes = async () => {
  loading.value = true
  try {
    const results = await Promise.all(
      props.items.map(async (item) => {
        try {
          const response = await apiGetRealtimePrice(item.code)
          console.log(`[TopVolumeList] ${item.code} response:`, response.data)
          const data = response.data.data
          return {
            code: item.code,
            name: data?.name || item.name,
            volume: data?.volume || 0,
            change: data?.change_percent ?? 0
          }
        } catch (e) {
          console.error(`[TopVolumeList] Error fetching ${item.code}:`, e)
          return {
            code: item.code,
            name: item.name,
            volume: 0,
            change: 0
          }
        }
      })
    )

    console.log('[TopVolumeList] All results:', results)

    // 거래량 기준 정렬
    topItems.value = results.sort((a, b) => b.volume - a.volume).slice(0, 5)
  } catch (e) {
    console.error('[TopVolumeList] Error:', e)
    error.value = '데이터를 가져올 수 없습니다'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchTopVolumes()
})
</script>

<style scoped>

.top-volume-list {
  width: 105%;
}
.card {
  background: rgba(255,255,255,0.85);
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 14px;
}

.card-title {
  font-size: 18px;
  font-weight: 800;
  margin: 0 0 12px 0;
}

.volume-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.volume-item {
  display: grid;
  grid-template-columns: 40px 1fr auto 40px;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.08);
  margin-bottom: 10px;
}

.rank {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #2563eb;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 14px;
}

.info {
  flex: 1;
}

.name {
  font-weight: 800;
  font-size: 15px;
}

.code {
  opacity: 0.7;
  font-size: 13px;
  margin-top: 2px;
}

.volume {
  text-align: right;
}

.amount {
  font-weight: 700;
  font-size: 15px;
}

.change {
  font-size: 13px;
  margin-top: 2px;
  font-weight: 600;
}

.change.positive {
  color: #ff4d4d;
}

.change.negative {
  color: #4d9eff;
}

.link {
  text-decoration: none;
  font-weight: 800;
  font-size: 20px;
  color: #2563eb;
}

.loading, .error {
  text-align: center;
  padding: 40px 20px;
  opacity: 0.7;
}

.error {
  color: #ef4444;
}
</style>
