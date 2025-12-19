<template>
  <div class="naver-wrapper">
    <NewsHeader
      v-model="query"
      :mode="mode"
      @search="search"
      @setMode="setMode"
    />

    <main class="naver-main">
      <NewsList
        :items="items"
        :selectedId="selectedId"
        @select="select"
        @toggleBookmark="toggleBookmark"
      />

      <NewsDetail :news="detail">
        <NewsSummary
          :disabled="!selectedId"
          :loading="loadingSummary"
          :summary="summary"
          @summarize="summarizeSelected"
        />
      </NewsDetail>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";
import { useNews } from "@/composables/news/useUi";

import NewsHeader from "@/components/news/NewsHeader.vue";
import NewsList from "@/components/news/NewsList.vue";
import NewsDetail from "@/components/news/NewsDetail.vue";
import NewsSummary from "@/components/news/NewsSummary.vue";

const router = useRouter();

const {
  query,
  mode,
  items,
  selectedId,
  detail,
  summary,
  loadingSummary,
  loadList,
  search,
  setMode,
  select,
  toggleBookmark,
  summarizeSelected,
} = useNews({
  onUnauthorized: () => router.push({ name: "login" }), // 401이면 로그인으로
});

// 최초 로딩
loadList();
</script>



<style src="@/assets/styles/news.css">

</style>