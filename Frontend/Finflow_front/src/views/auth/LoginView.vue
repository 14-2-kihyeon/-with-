<template>
  <div class="auth-page">
    <div class="auth-container">

      <!-- 로그인 카드 -->
      <div class="auth-card">
        <div class="card-header">
          <h2 class="card-title">로그인</h2>
          <p class="card-subtitle">계정에 로그인하여 서비스를 이용하세요</p>
        </div>

        <form @submit.prevent="onSubmit" class="auth-form">
          <!-- Username 입력 -->
          <div class="form-group">
            <label for="username" class="form-label">
              <span class="label-icon">👤</span>
              사용자명
            </label>
            <input
              id="username"
              v-model.trim="username"
              type="text"
              class="form-input"
              placeholder="사용자명을 입력하세요"
              required
              autocomplete="username"
            />
          </div>

          <!-- Password 입력 -->
          <div class="form-group">
            <label for="password" class="form-label">
              <span class="label-icon">🔒</span>
              비밀번호
            </label>
            <div class="password-input-wrapper">
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                class="form-input"
                placeholder="비밀번호를 입력하세요"
                required
                autocomplete="current-password"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="password-toggle"
              >
                {{ showPassword ? '👁️' : '👁️‍🗨️' }}
              </button>
            </div>
          </div>

          <!-- 에러 메시지 -->
          <div v-if="errorMsg" class="error-card">
            <span class="error-icon">⚠️</span>
            <div class="error-text">
              로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.
            </div>
          </div>

          <!-- 로그인 버튼 -->
          <button 
            type="submit" 
            class="btn-primary"
            :disabled="!username.trim() || !password"
          >
            <span class="btn-icon">🔓</span>
            로그인
          </button>
        </form>

        <!-- 회원가입 링크 -->
        <div class="auth-footer">
          <p class="footer-text">
            아직 계정이 없으신가요?
            <RouterLink to="/signup" class="footer-link">
              회원가입하기
            </RouterLink>
          </p>
        </div>
      </div>

      <!-- 보안 안내 -->
      <div class="security-notice">
        <span class="notice-icon">🛡️</span>
        <div class="notice-text">
          Personal Bank는 회원님의 정보를 안전하게 보호합니다.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()
const router = useRouter()

const username = ref("")
const password = ref("")
const errorMsg = ref("")
const showPassword = ref(false)

const onSubmit = async () => {
  errorMsg.value = ""
  try {
    await auth.login(username.value, password.value)
    router.push({ name: "mypage" })
  } catch (err) {
    errorMsg.value = JSON.stringify(err.response?.data || err.message)
    console.error("로그인 오류:", err)
  }
}
</script>

<style scoped>
/* 페이지 래퍼 */
.auth-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.auth-container {
  width: 100%;
  max-width: 440px;
}

/* 헤더 */
.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 12px;
}

.logo-icon {
  font-size: 2.5rem;
}

.logo-text {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 700;
  color: #3182f6;
}

.header-subtitle {
  margin: 0;
  font-size: 0.95rem;
  color: #6b7280;
}

/* 카드 */
.auth-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e8eb;
}

.card-header {
  text-align: center;
  margin-bottom: 32px;
}

.card-title {
  margin: 0 0 8px 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #191f28;
}

.card-subtitle {
  margin: 0;
  font-size: 0.9rem;
  color: #6b7280;
}

/* 폼 */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.95rem;
  font-weight: 600;
  color: #191f28;
}

.label-icon {
  font-size: 1rem;
}

.form-input {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #d1d5db;
  border-radius: 12px;
  font-size: 0.95rem;
  color: #191f28;
  background: #ffffff;
  transition: all 0.2s ease;
  font-family: inherit;
}

.form-input:focus {
  outline: none;
  border-color: #3182f6;
  box-shadow: 0 0 0 4px rgba(49, 130, 246, 0.1);
}

.form-input::placeholder {
  color: #9ca3af;
}

/* 비밀번호 입력 */
.password-input-wrapper {
  position: relative;
}

.password-input-wrapper .form-input {
  padding-right: 50px;
}

.password-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 1.3rem;
  cursor: pointer;
  padding: 4px 8px;
  transition: all 0.15s ease;
  border-radius: 6px;
}

.password-toggle:hover {
  background: #f3f4f6;
}

.password-toggle:active {
  transform: translateY(-50%) scale(0.95);
}

/* 에러 카드 */
.error-card {
  background: #fef2f2;
  border: 1.5px solid #fecaca;
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.error-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.error-text {
  font-size: 0.9rem;
  color: #991b1b;
  line-height: 1.5;
}

/* 버튼 */
.btn-primary {
  width: 100%;
  padding: 16px 24px;
  background: #3182f6;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(49, 130, 246, 0.3);
}

.btn-primary:hover:not(:disabled) {
  background: #1d6ee0;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(49, 130, 246, 0.4);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-icon {
  font-size: 1.1rem;
}

/* 푸터 */
.auth-footer {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e5e8eb;
  text-align: center;
}

.footer-text {
  margin: 0;
  font-size: 0.9rem;
  color: #6b7280;
}

.footer-link {
  color: #3182f6;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.15s ease;
}

.footer-link:hover {
  color: #1d6ee0;
  text-decoration: underline;
}

/* 보안 안내 */
.security-notice {
  margin-top: 20px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(229, 232, 235, 0.8);
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.notice-icon {
  font-size: 1.3rem;
  flex-shrink: 0;
}

.notice-text {
  font-size: 0.85rem;
  color: #6b7280;
  line-height: 1.5;
}

/* 반응형 */
@media (max-width: 640px) {
  .auth-card {
    padding: 32px 24px;
  }

  .logo-text {
    font-size: 1.5rem;
  }

  .card-title {
    font-size: 1.3rem;
  }

  .form-input {
    padding: 12px 14px;
  }

  .btn-primary {
    padding: 14px 20px;
  }
}

/* 애니메이션 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.auth-card {
  animation: fadeInUp 0.4s ease-out;
}

.security-notice {
  animation: fadeInUp 0.6s ease-out;
}
</style>