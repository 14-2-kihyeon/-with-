<template>
  <div class="stocks-market-tab">
    <!-- 탭 네비게이션 -->
    <div class="tabs">
      <RouterLink
        v-for="tab in tabs"
        :key="tab.value"
        :to="{ name: tab.route }"
        class="tab"
        :class="{ active: currentTab === tab.value }"
      >
        {{ tab.label }}
      </RouterLink>
    </div>

    <!-- 슬롯: 각 시장별 콘텐츠 -->
    <slot></slot>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  { label: '국내 주식', value: 'domestic', route: 'stocks_home' },
  { label: '해외 주식', value: 'global', route: 'stocks_global' },
  { label: '암호화폐', value: 'crypto', route: 'stocks_crypto' }
]

const currentTab = computed(() => {
  const routeName = route.name
  if (routeName === 'stocks_global') return 'global'
  if (routeName === 'stocks_crypto') return 'crypto'
  return 'domestic'
})
</script>

<style scoped>
.stocks-market-tab {
  max-width: 980px;
  margin: 0 auto;
  padding: 20px;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 14px;
  padding: 8px;
}

.tab {
  flex: 1;
  text-align: center;
  padding: 12px 20px;
  border-radius: 10px;
  text-decoration: none;
  font-weight: 700;
  transition: all 0.2s;
  color: rgba(0, 0, 0, 0.6);
}

.tab:hover {
  background: rgba(0, 0, 0, 0.05);
}

.tab.active {
  background: #2563eb;
  color: white;
}
</style>
