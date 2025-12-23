<template>
  <div class="auth-page">
    <div class="auth-container">
      <!-- 회원가입 카드 -->
      <div class="auth-card">
        <div class="card-header">
          <h2 class="card-title">회원가입</h2>
        </div>

        <form @submit.prevent="onSubmit" class="auth-form">
          <!-- Username 입력 -->
          <div class="form-group">
            <label for="username" class="form-label">
              <span class="label-icon">👤</span>
              사용자명
              <span class="required">*</span>
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
            <div class="field-hint">
              원하는 사용자명을 입력하세요
            </div>
          </div>

          <!-- Email 입력 -->
          <div class="form-group">
            <label for="email" class="form-label">
              <span class="label-icon">📧</span>
              이메일
            </label>
            <input
              id="email"
              v-model.trim="email"
              type="email"
              class="form-input"
              :class="{ 'input-error': emailError }"
              placeholder="example@email.com"
              autocomplete="email"
              @blur="validateEmail"
            />
            <div v-if="emailError" class="field-error">
              {{ emailError }}
            </div>
            <div v-else class="field-hint">
              비밀번호 찾기 등에 사용됩니다 (선택)
            </div>
          </div>

          <!-- Password 입력 -->
          <div class="form-group">
            <label for="password1" class="form-label">
              <span class="label-icon">🔒</span>
              비밀번호
              <span class="required">*</span>
            </label>
            <div class="password-input-wrapper">
              <input
                id="password1"
                v-model="password1"
                :type="showPassword1 ? 'text' : 'password'"
                class="form-input"
                :class="{ 'input-error': password1Error }"
                placeholder="8자 이상, 영문+숫자 조합"
                required
                autocomplete="new-password"
                @input="validatePassword1"
              />
              <button
                type="button"
                @click="showPassword1 = !showPassword1"
                class="password-toggle"
              >
                {{ showPassword1 ? '👁️' : '👁️‍🗨️' }}
              </button>
            </div>
            <div v-if="password1Error" class="field-error">
              {{ password1Error }}
            </div>
            <div v-else class="field-hint">
              안전한 비밀번호: 8자 이상, 영문+숫자 조합
            </div>
          </div>

          <!-- Password 확인 -->
          <div class="form-group">
            <label for="password2" class="form-label">
              <span class="label-icon">🔐</span>
              비밀번호 확인
              <span class="required">*</span>
            </label>
            <div class="password-input-wrapper">
              <input
                id="password2"
                v-model="password2"
                :type="showPassword2 ? 'text' : 'password'"
                class="form-input"
                :class="{ 'input-error': password2Error, 'input-success': password2Success }"
                placeholder="비밀번호를 다시 입력하세요"
                required
                autocomplete="new-password"
                @input="validatePassword2"
              />
              <button
                type="button"
                @click="showPassword2 = !showPassword2"
                class="password-toggle"
              >
                {{ showPassword2 ? '👁️' : '👁️‍🗨️' }}
              </button>
            </div>
            <div v-if="password2Error" class="field-error">
              {{ password2Error }}
            </div>
            <div v-else-if="password2Success" class="field-success">
              ✓ 비밀번호가 일치합니다
            </div>
          </div>

          <!-- 약관 동의 -->
          <div class="terms-group">
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="agreeTerms"
                class="checkbox-input"
              />
              <span class="checkbox-text">
                <span class="required">*</span>
                이용약관 및 개인정보처리방침에 동의합니다
              </span>
            </label>
          </div>

          <!-- 에러 메시지 -->
          <div v-if="errorMsg" class="error-card">
            <span class="error-icon">⚠️</span>
            <div class="error-text">
              {{ parseErrorMessage(errorMsg) }}
            </div>
          </div>

          <!-- 회원가입 버튼 -->
          <button 
            type="submit" 
            class="btn-primary"
            :disabled="!isFormValid"
          >
            <span class="btn-icon">✓</span>
            회원가입 완료
          </button>
        </form>

        <!-- 로그인 링크 -->
        <div class="auth-footer">
          <p class="footer-text">
            이미 계정이 있으신가요?
            <RouterLink to="/login" class="footer-link">
              로그인하기
            </RouterLink>
          </p>
        </div>
      </div>

      <!-- 보안 안내 -->
      <div class="security-notice">
        <span class="notice-icon">🛡️</span>
        <div class="notice-text">
          입력하신 개인정보는 암호화되어 안전하게 보관됩니다.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue"
import axios from "axios"
import { useRouter } from "vue-router"

const router = useRouter()
const username = ref("")
const email = ref("")
const password1 = ref("")
const password2 = ref("")
const errorMsg = ref("")
const agreeTerms = ref(false)

const showPassword1 = ref(false)
const showPassword2 = ref(false)

// 유효성 검사 에러
const emailError = ref("")
const password1Error = ref("")
const password2Error = ref("")
const password2Success = ref(false)

const API = "http://127.0.0.1:8000"

// 이메일 검증
const validateEmail = () => {
  if (!email.value) {
    emailError.value = ""
    return
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email.value)) {
    emailError.value = "올바른 이메일 형식이 아닙니다"
    return
  }
  emailError.value = ""
}

// 비밀번호 검증
const validatePassword1 = () => {
  if (!password1.value) {
    password1Error.value = ""
    return
  }
  if (password1.value.length < 8) {
    password1Error.value = "8자 이상 입력해주세요"
    return
  }
  if (!/(?=.*[a-zA-Z])(?=.*\d)/.test(password1.value)) {
    password1Error.value = "영문과 숫자를 모두 포함해주세요"
    return
  }
  password1Error.value = ""
  validatePassword2()
}

// 비밀번호 확인 검증
const validatePassword2 = () => {
  if (!password2.value) {
    password2Error.value = ""
    password2Success.value = false
    return
  }
  if (password1.value !== password2.value) {
    password2Error.value = "비밀번호가 일치하지 않습니다"
    password2Success.value = false
    return
  }
  password2Error.value = ""
  password2Success.value = true
}

// 폼 유효성 검사
const isFormValid = computed(() => {
  return (
    username.value.trim() &&
    !emailError.value &&
    password1.value &&
    !password1Error.value &&
    password2.value &&
    !password2Error.value &&
    password2Success.value &&
    agreeTerms.value
  )
})

// 에러 메시지 파싱
const parseErrorMessage = (error) => {
  try {
    const parsed = JSON.parse(error)
    if (parsed.username) return `사용자명: ${parsed.username[0]}`
    if (parsed.email) return `이메일: ${parsed.email[0]}`
    if (parsed.password1) return `비밀번호: ${parsed.password1[0]}`
    return "회원가입에 실패했습니다. 다시 시도해주세요."
  } catch {
    return "회원가입에 실패했습니다. 다시 시도해주세요."
  }
}

const onSubmit = async () => {
  // 최종 검증
  validateEmail()
  validatePassword1()
  validatePassword2()

  if (!isFormValid.value) {
    return
  }

  errorMsg.value = ""

  const payload = {
    username: username.value,
    password1: password1.value,
    password2: password2.value,
  }
  if (email.value) payload.email = email.value

  try {
    await axios.post(`${API}/accounts/registration/`, payload)
    alert("회원가입이 완료되었습니다! 로그인해주세요.")
    router.push({ name: "login" })
  } catch (err) {
    errorMsg.value = JSON.stringify(err.response?.data || err.message)
    console.error("회원가입 오류:", err)
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
  padding: 40px 20px;
}

.auth-container {
  width: 100%;
  max-width: 500px;
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
  line-height: 1.5;
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

.required {
  color: #ef4444;
  font-weight: 700;
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

.form-input.input-error {
  border-color: #ef4444;
}

.form-input.input-error:focus {
  box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.1);
}

.form-input.input-success {
  border-color: #10b981;
}

.form-input.input-success:focus {
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.1);
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

/* 필드 힌트/에러 */
.field-hint {
  font-size: 0.85rem;
  color: #6b7280;
}

.field-error {
  font-size: 0.85rem;
  color: #ef4444;
  font-weight: 500;
}

.field-success {
  font-size: 0.85rem;
  color: #10b981;
  font-weight: 500;
}

/* 약관 동의 */
.terms-group {
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e5e8eb;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.checkbox-input {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: #3182f6;
}

.checkbox-text {
  font-size: 0.9rem;
  color: #191f28;
  line-height: 1.5;
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
  .auth-page {
    padding: 20px;
  }

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