import { createRouter, createWebHistory } from "vue-router"
import { useAuthStore } from "@/stores/auth"
// 레이아웃
import MainLayout from "@/layouts/MainLayout.vue"
import FinLayout from "@/layouts/FinLayout.vue"

import MainView from "@/views/main/MainView.vue"

import LoginView from "@/views/auth/LoginView.vue"
import SignupView from "@/views/auth/SignupView.vue"
import MyPageView from "@/views/auth/MyPageView.vue"

import PostListView from "@/views/posts/PostListView.vue"
import PostDetailView from "@/views/posts/PostDetailView.vue"
import PostCreateView from "@/views/posts/PostCreateView.vue"
import PostEditView from "@/views/posts/PostEditView.vue"

import DepositListView from "@/views/finances/deposits/DepositListView.vue"
import DepositDetailView from "@/views/finances/deposits/DepositDetailView.vue"
import SavingListView from "@/views/finances/savings/SavingListView.vue"
import SavingDetailView from "@/views/finances/savings/SavingDetailView.vue"

import NaverNewsView from "@/views/news/NaverNewsView.vue"

import KakaoMapLayout from "@/layouts/KakaoMapLayout.vue"
import BankMapView from "@/views/kakaomap/BankMapView.vue"

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

        // ✅ posts (도메인 중첩)
        {
          path: "posts",
          children: [
            { path: "", name: "post_list", component: PostListView },
            { path: "create", name: "post_create", component: PostCreateView, meta: { requiresAuth: true } },
            { path: ":pk", name: "post_detail", component: PostDetailView, props: true },
            { path: ":pk/edit", name: "post_edit", component: PostEditView, meta: { requiresAuth: true }, props: true },
          ],
        },

        // ✅ finances (도메인 중첩)
        {
          path: "finances",
          component: FinLayout,
          children: [
            { path: "deposits", name: "deposit_list", component: DepositListView },
            { path: "deposits/:fin_prdt_cd", name: "deposit_detail", component: DepositDetailView, props: true },

            { path: "savings", name: "saving_list", component: SavingListView },
            { path: "savings/:fin_prdt_cd", name: "saving_detail", component: SavingDetailView, props: true },
          ],
        },

        // ✅ naver news
        { path: "naver", name: "naver_news", component: NaverNewsView },
        {
          path: "kakaomap",
          component: KakaoMapLayout,
          children: [
            { path: "", name: "bank_map", component: BankMapView },
          ],
        },
      ],
    },

    // 없는 주소 → 메인으로
    { path: "/:pathMatch(.*)*", redirect: { name: "main" } },

  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // 새로고침 후 토큰은 있는데 user 없으면 복구
  if (auth.isLogin && !auth.user) {
    try { await auth.fetchUser() } catch {}
  }

  if (to.meta.requiresAuth && !auth.isLogin) {
    return { name: "login" }
  }
})

export default router
