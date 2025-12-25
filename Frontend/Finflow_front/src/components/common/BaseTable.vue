

<!-- 표(Table) UI를 재사용하려고 만든 공용 컴포넌트 -->


<template>
  <table class="app-table">
    <thead>
      <tr>
        <th v-for="col in columns" :key="col.key">{{ col.label }}</th>
      </tr>
    </thead>

    <tbody>
      <tr
        v-for="row in rows"
        :key="row[rowKey]"
        class="row"
        @click="$emit('rowClick', row)"
      >
        <td v-for="col in columns" :key="col.key">
          <slot :name="`cell-${col.key}`" :row="row">
            {{ row[col.key] }}
          </slot>
        </td>
      </tr>

      <tr v-if="rows.length === 0">
        <td :colspan="columns.length" class="empty">데이터가 없습니다.</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
defineProps({
  columns: { type: Array, required: true }, // [{key,label}]
  rows: { type: Array, default: () => [] },
  rowKey: { type: String, default: "id" },
})
defineEmits(["rowClick"])
</script>

<style scoped>
.row { cursor: pointer; }
.empty { text-align:center; padding:16px; }
</style>

