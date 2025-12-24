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
        <!-- 항상 표시되는 주요 메뉴 -->
        <RouterLink :to="{ name: 'fin_home' }" class="nav-link main-menu">예적금</RouterLink>
        <RouterLink :to="{ name: 'stocks_home' }" class="nav-link main-menu">주식</RouterLink>
        <RouterLink :to="{ name: 'naver_news' }" class="nav-link main-menu">뉴스</RouterLink>
        <RouterLink :to="{ name: 'post_list' }" class="nav-link main-menu">커뮤니티</RouterLink>

        <!-- 작은 화면에서 숨겨지는 메뉴 -->
        <RouterLink :to="{ name: 'bank_map' }" class="nav-link hide-mobile">지도</RouterLink>
        <RouterLink :to="{ name: 'youtube_search' }" class="nav-link hide-mobile">유튜브</RouterLink>
        <RouterLink v-if="auth.isLogin" :to="{ name: 'investment_survey' }" class="nav-link hide-mobile">투자 성향 검사</RouterLink>
        <RouterLink v-if="auth.isLogin" :to="{ name: 'recommendations' }" class="nav-link hide-mobile">맞춤 추천</RouterLink>

        <!-- 더보기 드롭다운 (작은 화면에서만 표시) -->
        <div class="more-menu" ref="moreArea">
          <button class="nav-link more-btn" @click="toggleMoreMenu">
            더보기
            <span class="chev" :class="{ open: isMoreOpen }">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none">
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

          <div v-if="isMoreOpen" class="more-dropdown">
            <RouterLink :to="{ name: 'bank_map' }" class="dropdown-item" @click="closeMoreMenu">지도</RouterLink>
            <RouterLink :to="{ name: 'youtube_search' }" class="dropdown-item" @click="closeMoreMenu">유튜브</RouterLink>
            <RouterLink v-if="auth.isLogin" :to="{ name: 'investment_survey' }" class="dropdown-item" @click="closeMoreMenu">투자 성향 검사</RouterLink>
            <RouterLink v-if="auth.isLogin" :to="{ name: 'recommendations' }" class="dropdown-item" @click="closeMoreMenu">맞춤 추천</RouterLink>
          </div>
        </div>
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
const isMoreOpen = ref(false)
const moreArea = ref(null)

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}
const closeDropdown = () => {
  isOpen.value = false
}

const toggleMoreMenu = () => {
  isMoreOpen.value = !isMoreOpen.value
}
const closeMoreMenu = () => {
  isMoreOpen.value = false
}

const onLogout = async () => {
  closeDropdown()
  await auth.logout()
  router.push({ name: "main" })
}

// 바깥 클릭 시 드롭다운 닫기
const onClickOutside = (e) => {
  if (userArea.value && !userArea.value.contains(e.target)) {
    closeDropdown()
  }
  if (moreArea.value && !moreArea.value.contains(e.target)) {
    closeMoreMenu()
  }
}

onMounted(() => {
  window.addEventListener("click", onClickOutside)
})

onBeforeUnmount(() => {
  window.removeEventListener("click", onClickOutside)
})

// 라우트 이동 시 모든 드롭다운 닫기
watch(
  () => router.currentRoute.value.fullPath,
  () => {
    closeDropdown()
    closeMoreMenu()
  }
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

  /* 항상 흰색 */
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
  gap: 120px; /* 로고와 메뉴 사이 간격 확대 */
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

  /* 메탈릭 스타일: 각진 형태 + 그라데이션 테두리 */
  border: 1.5px solid;
  border-image: linear-gradient(135deg, #94a3b8, #cbd5e1, #e2e8f0) 1;
  background: linear-gradient(145deg, #ffffff, #f8fafc);
  color: #0f172a;

  padding: 9px 14px;
  border-radius: 4px; /* 각진 형태 */
  cursor: pointer;

  transition: all 0.2s ease;
  box-shadow:
    0 1px 3px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}
.user-btn:hover {
  background: linear-gradient(145deg, #f8fafc, #f1f5f9);
  border-image: linear-gradient(135deg, #64748b, #94a3b8, #cbd5e1) 1;
  box-shadow:
    0 4px 12px rgba(15, 23, 42, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 1);
  transform: translateY(-1px);
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

/* 드롭다운 - 메탈릭 각진 스타일 */
.dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 10px);
  min-width: 180px;

  /* 메탈릭 각진 스타일 */
  background: linear-gradient(145deg, #ffffff, #f8fafc);
  border: 1.5px solid;
  border-image: linear-gradient(135deg, #94a3b8, #cbd5e1, #e2e8f0) 1;
  border-radius: 4px; /* 각진 형태 */
  box-shadow:
    0 8px 24px rgba(15, 23, 42, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
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

  padding: 10px 12px;
  border-radius: 3px; /* 각진 형태 */

  color: #0f172a;
  font-size: 14px;
  font-weight: 600;

  transition: all 0.2s ease;
}

.dropdown-item:hover {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(59, 130, 246, 0.05));
  color: #1d4ed8;
  box-shadow: inset 0 1px 2px rgba(37, 99, 235, 0.1);
}

.dropdown-item.danger:hover {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.10), rgba(248, 113, 113, 0.08));
  color: #ef4444;
  box-shadow: inset 0 1px 2px rgba(239, 68, 68, 0.15);
}

/* 더보기 메뉴 */
.more-menu {
  position: relative;
  display: none; /* 기본적으로 숨김 */
}

.more-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  cursor: pointer;
  white-space: nowrap;
}

.more-dropdown {
  position: absolute;
  left: 0;
  top: calc(100% + 10px);
  min-width: 200px;
  z-index: 100;

  /* 드롭다운 스타일 통일 */
  background: linear-gradient(145deg, #ffffff, #f8fafc);
  border: 1.5px solid;
  border-image: linear-gradient(135deg, #94a3b8, #cbd5e1, #e2e8f0) 1;
  border-radius: 4px;
  box-shadow:
    0 8px 24px rgba(15, 23, 42, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  overflow: hidden;
  padding: 6px;
}

/* 반응형: 큰 화면 (1140px 초과) - 모든 메뉴 표시 */
@media (min-width: 1141px) {
  .hide-mobile {
    display: block;
  }
  .more-menu {
    display: none;
  }
}

/* 반응형: 1140px 이하 - 주요 메뉴 4개 + 더보기 */
@media (max-width: 1140px) {
  .menu {
    flex-wrap: nowrap;
    overflow: visible;
  }

  .nav-link {
    white-space: nowrap;
  }

  .hide-mobile {
    display: none;
  }

  .more-menu {
    display: block;
  }
}

/* 중간 화면 (683px ~ 1140px) */
@media (min-width: 683px) and (max-width: 1140px) {
  .nav-inner {
    gap: 40px;
  }

  .menu {
    gap: 10px;
  }

  .nav-link {
    font-size: 13px;
    padding: 6px 6px;
  }
}

/* 작은 화면 (481px ~ 682px) - 사용자 이름 숨김 */
@media (min-width: 481px) and (max-width: 682px) {
  .nav-inner {
    gap: 20px;
    padding: 0 12px;
  }

  .brand-logo {
    height: 18px;
    max-width: 150px;
  }

  .menu {
    gap: 6px;
  }

  .nav-link {
    font-size: 11px;
    padding: 5px 4px;
  }

  .user-name {
    display: none;
  }

  .user-btn {
    padding: 7px 10px;
  }

  .auth-link {
    font-size: 11px;
    padding: 5px 6px;
  }
}

/* 초소형 화면 (480px 이하) */
@media (max-width: 480px) {
  .nav-inner {
    gap: 12px;
    padding: 0 10px;
  }

  .brand-logo {
    height: 16px;
    max-width: 120px;
  }

  .menu {
    gap: 5px;
  }

  .nav-link {
    font-size: 10px;
    padding: 4px 3px;
  }

  .more-btn {
    font-size: 10px;
  }

  .user-name {
    display: none;
  }

  .user-btn {
    padding: 6px 8px;
  }

  .auth-link {
    font-size: 10px;
    padding: 4px 5px;
  }
}
</style>
