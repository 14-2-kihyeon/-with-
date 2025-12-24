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

  </main>



</template>


<script setup>
import FeatureSection from "@/components/main/FeatureSection.vue"

/**
 * 캡쳐 이미지 경로는 네 프로젝트 상황에 맞게 바꿔줘.
 * 일단은 /src/assets/main/... 에 파일을 넣고 아래처럼 import 해서 쓰는 방식이 가장 단순해.
 */
import posts1 from "@/assets/main/posts/posts1.png"
import posts2 from "@/assets/main/posts/posts2.png"
import posts3 from "@/assets/main/posts/posts3.png"

import finances1 from "@/assets/main/finances/fin1.png"
import finances2 from "@/assets/main/finances/fin2.png"
import finances3 from "@/assets/main/finances/fin3.png"

import news1 from "@/assets/main/news/news1.png"
import news2 from "@/assets/main/news/news2.png"
import news3 from "@/assets/main/news/news3.png"

import kakao1 from "@/assets/main/kakaomap/kakao1.png"
import kakao2 from "@/assets/main/kakaomap/kakao2.png"
import kakao3 from "@/assets/main/kakaomap/kakao3.png"

import youtube1 from "@/assets/main/youtube/youtube1.png"
import youtube2 from "@/assets/main/youtube/youtube2.png"
import youtube3 from "@/assets/main/youtube/youtube3.png"

import chatbot1 from "@/assets/main/chatbot/chatbot1.png"
import chatbot2 from "@/assets/main/chatbot/chatbot2.png"
import chatbot3 from "@/assets/main/chatbot/chatbot3.png"

import pbti1 from "@/assets/main/pbti/pbti1.png"
import pbti2 from "@/assets/main/pbti/pbti2.png"
import pbti3 from "@/assets/main/pbti/pbti3.png"

import stock1 from "@/assets/main/stock/stock1.png"
import stock2 from "@/assets/main/stock/stock2.png"
import stock3 from "@/assets/main/stock/stock3.png"


const features = [
  {
    key: "chatbot",
    title: "Chat-bot 상품 추천 서비스",
    description: "AI Chat-bot과의 대화로 내 상황과 조건에 맞는 상품을 추천 받을 수 있어요.",
    images: [chatbot1, chatbot2, chatbot3],
    routeName: "chatbot_list",
  },
  {
    key: "pbti",
    title: "PBTI 개인 투자 성향 테스트",
    description: "PBTI 검사로 나의 투자 성향을 파악할 수 있어요.",
    images: [pbti1, pbti2, pbti3],
    routeName: "pbti_list",
  },
  {
    key: "finances",
    title: "예금/적금/현물 상품 비교",
    description: "상품 리스트와 상세 옵션을 확인하고, 조건에 맞는 상품을 탐색할 수 있어요.",
    images: [finances1, finances2, finances3],
    routeName: "deposit_list",
  },
  {
    key: "stock",
    title: "주식",
    description: "카테고리 기반으로 글을 작성하고, 조회/수정/댓글을 관리할 수 있어요.",
    images: [stock1, stock2, stock3],
    routeName: "stock_list",
  },
  {
    key: "news",
    title: "네이버 뉴스",
    description: "키워드 기반으로 뉴스 정보를 검색하고 흐름을 빠르게 파악할 수 있어요.",
    images: [news1, news2, news3],
    routeName: "naver_news",
  },
  {
    key: "posts",
    title: "커뮤니티",
    description: "커뮤니티에서 다른 유저들과 소통하며 지식을 공유할 수 있어요.",
    images: [posts1, posts2, posts3],
    routeName: "post_list",
  },
  {
    key: "kakaomap",
    title: "내 주변 은행 찾기",
    description: "지도에서 주변 은행을 탐색하고 위치 기반으로 경로를 확인할 수 있어요.",
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