import { createRouter, createWebHistory } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { useFinSyncStore } from "@/stores/finSync"
// 레이아웃
import MainLayout from "@/layouts/MainLayout.vue"
import FinLayout from "@/layouts/FinLayout.vue"
// 메인
import MainView from "@/views/main/MainView.vue"
// Auth
import LoginView from "@/views/auth/LoginView.vue"
import SignupView from "@/views/auth/SignupView.vue"
import MyPageView from "@/views/auth/MyPageView.vue"
// Posts
import PostListView from "@/views/posts/PostListView.vue"
import PostDetailView from "@/views/posts/PostDetailView.vue"
import PostCreateView from "@/views/posts/PostCreateView.vue"
import PostEditView from "@/views/posts/PostEditView.vue"
// Finances
import FinHomeView from "@/views/finances/FinHomeView.vue"
import DepositDetailView from "@/views/finances/deposits/DepositDetailView.vue"
import SavingDetailView from "@/views/finances/savings/SavingDetailView.vue"
// News
import NaverNewsView from "@/views/news/NaverNewsView.vue"
// Kakaomap
import KakaoMapLayout from "@/layouts/KakaoMapLayout.vue"
import BankMapView from "@/views/kakaomap/BankMapView.vue"
// Youtube
import YoutubeLayout from "@/layouts/YoutubeLayout.vue"
import SearchView from "@/views/youtube/SearchView.vue"
import VideoDetailView from "@/views/youtube/VideoDetailView.vue"
// Survey
import InvestmentSurveyView from "@/views/auth/InvestmentSurveyView.vue"
import RecommendationsView from "@/views/auth/RecommendationsView.vue"
import Gold_SilverView from "@/views/finances/gold_silvers/Gold_SilverView.vue"
// Stocks
import StocksHomeView from "@/views/stocks/StocksHomeView.vue"
import StocksGlobalView from "@/views/stocks/StocksGlobalView.vue"
import StocksCryptoView from "@/views/stocks/StocksCryptoView.vue"
import StockDetailView from "@/views/stocks/StockDetailView.vue"


const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      component: MainLayout,
      children: [
        // ✅ 메인
        { path: "", name: "main", component: MainView },

        // ✅ auth
        { path: "login", name: "login", component: LoginView },
        { path: "signup", name: "signup", component: SignupView },
        { path: "mypage", name: "mypage", component: MyPageView, meta: { requiresAuth: true } },

        // ✅ posts 라우트 수정
        {
          path: "posts",
          children: [
            { path: "", name: "post_list", component: PostListView },
            { path: "create", name: "post_create", component: PostCreateView, meta: { requiresAuth: true } },
            {
              path: ":pk",
              name: "post_detail",
              component: PostDetailView,
              props: route => ({ pk: parseInt(route.params.pk) })
            },
            {
              path: ":pk/edit",
              name: "post_edit",
              component: PostEditView,
              meta: { requiresAuth: true },
              props: route => ({ pk: parseInt(route.params.pk) })
            },
          ],
        },

        // ✅ 투자 성향은 posts 밖으로 이동
        {
          path: "investment-survey",
          name: "investment_survey",
          component: InvestmentSurveyView,
          meta: { requiresAuth: true }
        },
        {
          path: "recommendations",
          name: "recommendations",
          component: RecommendationsView,
          meta: { requiresAuth: true }
        },

        // ✅ finances (도메인 중첩)
        {
          path: "finances",
          component: FinLayout,
          beforeEnter: (to) => {
            const finSync = useFinSyncStore()

            // fin_home 들어오면 기본 예금 최신화 트리거
            if (to.name === "fin_home") {
              finSync.ensureFresh("deposits")
              return
            }
          },
          children: [
            { path: "", name: "fin_home", component: FinHomeView },
            { path: "deposits/:fin_prdt_cd", name: "deposit_detail", component: DepositDetailView, props: true },
            { path: "savings/:fin_prdt_cd", name: "saving_detail", component: SavingDetailView, props: true },
            { path: "gold_silver/", name: "gold_silver", component: Gold_SilverView }
          ],
        },

        // ✅ naver news
        { path: "naver", name: "naver_news", component: NaverNewsView },
        // ✅ kakaomap
        {
          path: "kakaomap",
          component: KakaoMapLayout,
          children: [
            { path: "", name: "bank_map", component: BankMapView },
          ],
        },
        // ✅ youtube
        {
          path: "youtube",
          component: YoutubeLayout,
          children: [
            { path: "", redirect: { name: "youtube_search" } },
            { path: "search", name: "youtube_search", component: SearchView },
            { path: "video/:id", name: "youtube_detail", component: VideoDetailView, props: true },
            { path: "saved", name: "youtube_saved", component: () => import("@/views/youtube/SavedVideosView.vue") },
            { path: "channels", name: "youtube_channels", component: () => import("@/views/youtube/ChannelsView.vue") },
          ],
        },
        // ✅ stocks (국내/해외/암호화폐)
        {
          path: "stocks",
          children: [
            { path: "", name: "stocks_home", component: StocksHomeView },
            { path: "global", name: "stocks_global", component: StocksGlobalView },
            { path: "crypto", name: "stocks_crypto", component: StocksCryptoView },
            { path: ":code", name: "stock_detail", component: StockDetailView, props: true },
          ],
        },
      ],
    },

    // 없는 주소 → 메인으로
    { path: "/:pathMatch(.*)*", redirect: { name: "main" } },

  ],
  scrollBehavior(to, from, savedPosition) {
    // 뒤로가기 등: 기존 위치 복원
    if (savedPosition) return savedPosition

    // ✅ main으로 갈 때는 항상 맨 위
    if (to.name === "main") return { top: 0, left: 0 }

    // 나머지는 기본적으로 맨 위(원하면 제거 가능)
    return { top: 0, left: 0 }
  },
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // 새로고침 후 토큰은 있는데 user 없으면 복구
  if (auth.isLogin && !auth.user) {
    try { await auth.fetchUser() } catch { }
  }

  if (to.meta.requiresAuth && !auth.isLogin) {
    return { name: "login" }
  }
})

export default router
