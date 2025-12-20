<template>
  <main class="home">
    <!-- 1) 처음 들어왔을 때 소개 -->
    <section class="home-hero">
      <div class="home-hero__inner">
        <h1 class="home-hero__title">Finflow</h1>
        <p class="home-hero__desc">
          예·적금 비교부터 투자 성향 기반 추천, 뉴스/지도/유튜브 기능까지
          금융 생활을 한 곳에서 관리하는 통합 서비스입니다.
        </p>

        <div class="home-hero__hint">
          아래로 스크롤해서 기능을 확인하세요 ↓
        </div>
      </div>
    </section>

    <!-- 2) 스크롤 내려가며 기능 소개 -->
    <FeatureSection
      v-for="(f, i) in features"
      :key="f.key"
      :title="f.title"
      :description="f.description"
      :images="f.images"
      :route-name="f.routeName"
      :reverse="i % 2 === 1"
      :interval-ms="2600"
    />
  </main>



</template>


<script setup>
import { useAuthStore } from "@/stores/auth"
const auth = useAuthStore()








import FeatureSection from "@/components/main/FeatureSection.vue"

/**
 * ✅ 캡쳐 이미지 경로는 네 프로젝트 상황에 맞게 바꿔줘.
 * 일단은 /src/assets/main/... 에 파일을 넣고 아래처럼 import 해서 쓰는 방식이 가장 단순해.
 */
import posts1 from "@/assets/main/posts/posts1.jfif"
import posts2 from "@/assets/main/posts/posts2.jfif"
import posts3 from "@/assets/main/posts/posts3.jfif"

import finances1 from "@/assets/main/finances/fin1.jfif"
import finances2 from "@/assets/main/finances/fin2.jfif"
import finances3 from "@/assets/main/finances/fin3.jfif"

import news1 from "@/assets/main/news/news1.jfif"
import news2 from "@/assets/main/news/news2.jfif"
import news3 from "@/assets/main/news/news3.jfif"

import kakao1 from "@/assets/main/kakaomap/kakao1.jfif"
import kakao2 from "@/assets/main/kakaomap/kakao2.jfif"
import kakao3 from "@/assets/main/kakaomap/kakao3.jfif"

import youtube1 from "@/assets/main/youtube/youtube1.jfif"
import youtube2 from "@/assets/main/youtube/youtube2.jfif"
import youtube3 from "@/assets/main/youtube/youtube3.jfif"


const features = [
  {
    key: "posts",
    title: "게시판",
    description: "카테고리 기반으로 글을 작성하고, 조회/수정/댓글을 관리할 수 있어요.",
    images: [posts1, posts2, posts3],
    routeName: "post_list",
  },
  {
    key: "finances",
    title: "예금/적금 상품 비교",
    description: "상품 리스트와 상세 옵션을 확인하고, 조건에 맞는 상품을 탐색할 수 있어요.",
    images: [finances1, finances2, finances3],
    routeName: "deposit_list",
  },
  {
    key: "news",
    title: "네이버 뉴스",
    description: "키워드 기반으로 뉴스 정보를 검색하고 흐름을 빠르게 파악할 수 있어요.",
    images: [news1, news2, news3],
    routeName: "naver_news",
  },
  {
    key: "kakaomap",
    title: "카카오맵 은행 찾기",
    description: "지도에서 주변 은행을 탐색하고 위치 기반으로 확인할 수 있어요.",
    images: [kakao1, kakao2, kakao3],
    routeName: "bank_map",
  },
  {
    key: "youtube",
    title: "유튜브 검색/저장",
    description: "금융 학습 영상을 검색하고 저장해서 나만의 학습 리스트를 만들 수 있어요.",
    images: [youtube1, youtube2, youtube3],
    routeName: "youtube_search",
  },
]
</script>

<style scoped>
.home {
  /* mandatory는 딱딱 끊기는데, 내용이 적으면 공백이 더 커 보입니다 */
  scroll-snap-type: y proximity;
  overflow-x: hidden;
}

/* Hero: 너무 길게 잡혀서 밑에 공백이 큼 */
.home-hero {
  min-height: 60vh;          /* 80~100vh였다면 확 줄여 */
  display: grid;
  align-items: start;
  padding: 28px 18px 12px;   /* 아래 패딩도 줄임 */
  scroll-snap-align: start;
}

.home-hero__inner {
  max-width: 900px;
  margin: 0 auto;
  padding-top: 16px;         /* 내려와 보이면 이 값만 더 줄이기(예: 8px) */
}

.home-hero__title {
  font-size: 56px;
  margin: 0 0 10px;
}
.home-hero__desc {
  margin: 0 0 10px;
  font-size: 18px;
  line-height: 1.7;
  opacity: 0.9;
}
.home-hero__hint {
  opacity: 0.75;
}

</style>