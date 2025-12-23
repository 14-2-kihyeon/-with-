<template>
  <main class="home">

    <!-- 스크롤 내려가며 기능 소개 -->
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

    <!-- AI 챗봇 위젯 -->
    <ChatbotWidget v-if="auth.isLogin" />
  </main>



</template>


<script setup>
import { useAuthStore } from "@/stores/auth"
const auth = useAuthStore()


import FeatureSection from "@/components/main/FeatureSection.vue"
import ChatbotWidget from "@/components/common/ChatbotWidget.vue"

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


</style>