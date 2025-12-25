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
    title: "나만의 개인 챗봇",
    description: "AI Chat-bot?!\n나에게 딱 맞는\n금융 상품은 뭘까?",
    images: [chatbot1, chatbot2, chatbot3],
    routeName: "chatbot_list",
  },
  {
    key: "pbti",
    title: "PBTI 개인 투자 성향 테스트",
    description: "PBTI 검사로\n평소 나의 투자 성향\n파악하기",
    images: [pbti1, pbti2, pbti3],
    routeName: "investment_survey",
  },
  {
    key: "finances",
    title: "예금/적금/현물 상품 비교",
    description: "예적금 상품들의\n상세 옵션과\n현물 시세 비교까지\n한눈에!",
    images: [finances1, finances2, finances3],
    routeName: "fin_home",
  },
  {
    key: "stock",
    title: "주식",
    description: "국내외 주식 차트를\n비교하고\nAI 설명까지",
    images: [stock1, stock2, stock3],
    routeName: "stocks_home",
  },
  {
    key: "news",
    title: "네이버 뉴스",
    description: "키워드 기반\n뉴스 정보 검색\nAI 요약까지!",
    images: [news1, news2, news3],
    routeName: "naver_news",
  },
  {
    key: "posts",
    title: "커뮤니티",
    description: "다른 유저들과 소통하며\n서로의 금융 지식을\n공유하세요.",
    images: [posts1, posts2, posts3],
    routeName: "post_list",
  },
  {
    key: "kakaomap",
    title: "내 주변 은행 찾기",
    description: "지도에서\n가까운 은행 지점을\n찾을 수 있어요.",
    images: [kakao1, kakao2, kakao3],
    routeName: "bank_map",
  },
  {
    key: "youtube",
    title: "유튜브 검색/저장",
    description: "금융 학습 영상을\n찾고 저장해서\n나만의 리스트를\n만들 수 있어요.",
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