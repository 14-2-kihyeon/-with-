<template>
  <div>
    <NavBar />
    <main class="app-container">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import NavBar from "@/components/common/NavBar.vue"
</script>

<style scoped>
.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px;
}
</style>
