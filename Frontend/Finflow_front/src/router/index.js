import { createRouter, createWebHistory } from "vue-router"
import { useAuthStore } from "@/stores/auth"

import MainView from "@/views/main/MainView.vue"

import LoginView from "@/views/auth/LoginView.vue"
import SignupView from "@/views/auth/SignupView.vue"
import MyPageView from "@/views/auth/MyPageView.vue"

// Posts 4개
import PostListView from "@/views/posts/PostListView.vue"
import PostDetailView from "@/views/posts/PostDetailView.vue"
import PostCreateView from "@/views/posts/PostCreateView.vue"
import PostEditView from "@/views/posts/PostEditView.vue"

const router = createRouter({
  history: createWebHistory(),
  routes: [
        // ✅ 메인
    { path: "/", name: "main", component: MainView },

        // ✅ auth
    { path: "/login", name: "login", component: LoginView },
    { path: "/signup", name: "signup", component: SignupView },
    { path: "/mypage", name: "mypage", component: MyPageView, meta: { requiresAuth: true } },

        // ✅ posts
    { path: "/posts", name: "post_list", component: PostListView },
    { path: "/posts/create", name: "post_create", component: PostCreateView, meta: { requiresAuth: true } },
    { path: "/posts/:pk", name: "post_detail", component: PostDetailView, props: true },
    { path: "/posts/:pk/edit", name: "post_edit", component: PostEditView, meta: { requiresAuth: true }, props: true },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // 새로고침 후 토큰이 있는데 user가 없으면 복구
  if (auth.isLogin && !auth.user) {
    try { await auth.fetchUser() } catch {}
  }

  if (to.meta.requiresAuth && !auth.isLogin) {
    return { name: "login" }
  }
})

export default router
