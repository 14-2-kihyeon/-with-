<template>
  <header class="header" :class="{ 'header--scrolled': scrolled }">
    <nav class="nav-inner">
      <!-- Left: Logo -->
      <RouterLink :to="{ name: 'main' }" class="brand" aria-label="Home">
        <!-- 간단 로고(원하면 이미지로 교체 가능) -->
        <img class="brand-logo" src="@/assets/navbar/logo.png" alt="Personal Bank" />
      </RouterLink>

      <!-- Center: Menus -->
      <div class="menu">
        <RouterLink :to="{ name: 'post_list' }" class="nav-link">Posts</RouterLink>
        <RouterLink :to="{ name: 'deposit_list' }" class="nav-link">Deposits</RouterLink>
        <RouterLink :to="{ name: 'saving_list' }" class="nav-link">Savings</RouterLink>
        <RouterLink :to="{ name: 'naver_news' }" class="nav-link">Naver News</RouterLink>
        <RouterLink :to="{ name: 'bank_map' }" class="nav-link">KaKao Map</RouterLink>
        <RouterLink :to="{ name: 'youtube_search' }" class="nav-link">YouTube</RouterLink>
        <RouterLink :to="{ name: 'stocks_home' }" class="nav-link">Stocks</RouterLink>

        <RouterLink
          v-if="auth.isLogin"
          :to="{ name: 'investment_survey' }"
          class="nav-link"
        >
          투자 성향 검사
        </RouterLink>
        <RouterLink
          v-if="auth.isLogin"
          :to="{ name: 'recommendations' }"
          class="nav-link"
        >
          맞춤 추천
        </RouterLink>
      </div>

      <!-- Right: Auth -->
      <div class="right">
        <template v-if="auth.isLogin">
          <div class="user" ref="userArea">
            <button class="user-btn" type="button" @click="toggleDropdown">
              <span class="user-icon" aria-hidden="true">
                <!-- 사용자 아이콘 SVG -->
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
                  <path
                    d="M12 12a4.5 4.5 0 1 0-4.5-4.5A4.5 4.5 0 0 0 12 12Z"
                    stroke="currentColor"
                    stroke-width="1.6"
                  />
                  <path
                    d="M4.5 20c1.6-4.3 13.4-4.3 15 0"
                    stroke="currentColor"
                    stroke-width="1.6"
                    stroke-linecap="round"
                  />
                </svg>
              </span>

              <span class="user-name">
                {{ auth.user?.username || "loading..." }}
              </span>

              <span class="chev" :class="{ open: isOpen }" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
                  <path
                    d="M7 10l5 5 5-5"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </span>
            </button>

            <div v-if="isOpen" class="dropdown" role="menu">
              <RouterLink
                :to="{ name: 'mypage' }"
                class="dropdown-item"
                role="menuitem"
                @click="closeDropdown"
              >
                마이페이지
              </RouterLink>

              <button class="dropdown-item danger" type="button" @click="onLogout">
                로그아웃
              </button>
            </div>
          </div>
        </template>

        <template v-else>
          <RouterLink :to="{ name: 'login' }" class="nav-link auth-link">Login</RouterLink>
          <RouterLink :to="{ name: 'signup' }" class="nav-link auth-link">Signup</RouterLink>
        </template>
      </div>
    </nav>
  </header>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()
const router = useRouter()

const isOpen = ref(false)
const userArea = ref(null)

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}
const closeDropdown = () => {
  isOpen.value = false
}

const onLogout = async () => {
  closeDropdown()
  await auth.logout()
  router.push({ name: "main" })
}

// 바깥 클릭 시 드롭다운 닫기
const onClickOutside = (e) => {
  if (!userArea.value) return
  if (!userArea.value.contains(e.target)) closeDropdown()
}

onMounted(() => {
  window.addEventListener("click", onClickOutside)
})

onBeforeUnmount(() => {
  window.removeEventListener("click", onClickOutside)
})

// 라우트 이동 시 드롭다운 닫기
watch(
  () => router.currentRoute.value.fullPath,
  () => closeDropdown()
)

defineProps({
  scrolled: { type: Boolean, default: false }
})
</script>

<style scoped>
/* 상단 고정 헤더 */
.header {
  position: sticky;
  top: 0;
  z-index: 1000;

  /* ✅ 항상 흰색 */
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);

  border-bottom: 1px solid rgba(15, 23, 42, 0.10);
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);

  /* 스크롤 변화 없으니 transition도 없어도 됨 */
}

.header--scrolled {
  background: rgba(255, 255, 255, 0.92);
  border-bottom-color: rgba(15, 23, 42, 0.10);
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
}

/* 내부 정렬 */
.nav-inner {
  height: 60px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;

  display: flex;
  align-items: center;
  gap: 16px;
}

/* 로고 */
.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: #0f172a;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.brand-logo {
  height: 22px;      /* 높이만 고정 */
  width: auto;       /* 가로는 비율대로 */
  max-width: 260px;  /* 너무 길어지는 것 방지 */
  object-fit: contain;
  display: block;
}
.brand-text {
  font-size: 18px;
}

/* 메뉴 */
.menu {
  display: flex;
  align-items: center;
  gap: 18px;
  flex: 1;
  overflow: hidden;
}

/* 링크 기본 */
.nav-link {
  position: relative;
  text-decoration: none;
  color: #334155;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 6px;
  border-radius: 10px;
  transition: background 0.15s ease, color 0.15s ease;
}

/* Hover 차이(요구사항) */
.nav-link:hover {
  background: rgba(37, 99, 235, 0.08);
  color: #1d4ed8;
}

/* 활성 라우트 강조 */
.nav-link.router-link-active {
  color: #0f172a;
  font-weight: 700;
}

/* 우측 */
.right {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 로그인/회원가입 링크는 살짝 버튼 느낌 */
.auth-link {
  padding: 8px 10px;
}

/* 사용자 영역 */
.user {
  position: relative;
}

.user-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;

  border: 1px solid rgba(15, 23, 42, 0.12);
  background: #fff;
  color: #0f172a;

  padding: 8px 10px;
  border-radius: 12px;
  cursor: pointer;

  transition: box-shadow 0.15s ease, border-color 0.15s ease;
}
.user-btn:hover {
  border-color: rgba(37, 99, 235, 0.35);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
}

.user-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #334155;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.chev {
  display: inline-flex;
  transition: transform 0.15s ease;
  color: #475569;
}
.chev.open {
  transform: rotate(180deg);
}

/* 드롭다운 */
.dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 10px);
  min-width: 180px;

  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.12);
  border-radius: 14px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
  overflow: hidden;
  padding: 6px;
}

.dropdown-item {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;

  text-decoration: none;
  background: transparent;
  border: none;
  cursor: pointer;

  padding: 10px 10px;
  border-radius: 10px;

  color: #0f172a;
  font-size: 14px;
  font-weight: 600;

  transition: background 0.15s ease, color 0.15s ease;
}

.dropdown-item:hover {
  background: rgba(37, 99, 235, 0.08);
  color: #1d4ed8;
}

.dropdown-item.danger:hover {
  background: rgba(239, 68, 68, 0.10);
  color: #ef4444;
}

/* 모바일에서 메뉴가 너무 길면 줄바꿈/스크롤 등 추가 조정 필요 */
@media (max-width: 900px) {
  .menu {
    gap: 10px;
    overflow-x: auto;
    white-space: nowrap;
  }
}
</style>
