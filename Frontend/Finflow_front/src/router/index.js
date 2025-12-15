// src/router/index.js
import { createRouter, createWebHistory } from "vue-router"
import { useAuthStore } from "@/stores/auth"
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
import DepositListView from "@/views/finances/deposits/DepositListView.vue"
import DepositDetailView from "@/views/finances/deposits/DepositDetailView.vue"
import SavingListView from "@/views/finances/savings/SavingListView.vue"
import SavingDetailView from "@/views/finances/savings/SavingDetailView.vue"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      component: MainLayout,
      children: [
        { path: "", name: "main", component: MainView },

        // auth
        { path: "login", name: "login", component: LoginView },
        { path: "signup", name: "signup", component: SignupView },
        { path: "mypage", name: "mypage", component: MyPageView, meta: { requiresAuth: true } },

        // posts
        { path: "posts", name: "post_list", component: PostListView },
        { path: "posts/create", name: "post_create", component: PostCreateView, meta: { requiresAuth: true } },
        { path: "posts/:pk", name: "post_detail", component: PostDetailView, props: true },
        { path: "posts/:pk/edit", name: "post_edit", component: PostEditView, meta: { requiresAuth: true }, props: true },

        // finances (예금/적금 공통 레이아웃)
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
      ],
    },
  ],
})

// ✅ nested meta 대응: to.matched 로 검사
router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (auth.isLogin && !auth.user) {
    try { await auth.fetchUser() } catch {}
  }

  const needAuth = to.matched.some((r) => r.meta?.requiresAuth)
  if (needAuth && !auth.isLogin) return { name: "login" }
})

export default router
