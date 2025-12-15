<!-- src/layouts/MainLayout.vue -->
<template>
  <div>
    <NavBar />
    <main class="page">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import NavBar from "@/components/common/NavBar.vue"
</script>


<style scoped>

</style>