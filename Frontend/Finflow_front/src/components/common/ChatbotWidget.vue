<template>
  <div class="chatbot-widget">
    <!-- 플로팅 버튼 -->
    <transition name="bounce">
      <button
        v-if="!isOpen"
        @click="toggleChat"
        class="chatbot-floating-btn"
        :class="{ 'pulse': hasNewRecommendation }"
      >
        <img :src="avatarImage" alt="AI 챗봇" class="chatbot-avatar-icon" @error="handleImageError" />
        <span v-if="hasNewRecommendation" class="notification-badge">!</span>
      </button>
    </transition>

    <!-- 채팅 창 -->
    <transition name="slide-up">
      <div v-if="isOpen" class="chatbot-container" ref="chatContainer" :style="containerStyle">
        <!-- 리사이즈 핸들 -->
        <div class="resize-handle resize-handle-top" @mousedown="startResize('top', $event)"></div>
        <div class="resize-handle resize-handle-left" @mousedown="startResize('left', $event)"></div>
        <div class="resize-handle resize-handle-top-left" @mousedown="startResize('top-left', $event)"></div>

        <!-- 헤더 -->
        <div class="chatbot-header">
          <div class="header-left">
            <img :src="avatarImage" alt="AI 챗봇" class="chatbot-avatar" />
            <div class="header-text">
              <h4 class="chatbot-title">Finflow AI 상담사</h4>
              <p class="chatbot-subtitle" v-if="riskType">{{ riskTypeLabel }} 투자자</p>
              <p class="chatbot-subtitle" v-else>투자 성향 분석 필요</p>
            </div>
          </div>
          <button @click="toggleChat" class="close-btn">&times;</button>
        </div>

        <!-- 메시지 영역 -->
        <div class="chatbot-messages" ref="messagesContainer">
          <!-- 초기 안내 메시지 -->
          <div v-if="messages.length === 0" class="welcome-message">
            <img :src="avatarImage" alt="AI" class="welcome-avatar" />
            <div class="welcome-text">
              <h5>안녕하세요! Finflow AI 상담사입니다.</h5>
              <p>금융 상품 추천, 투자 조언 등 무엇이든 물어보세요.</p>
              <div class="quick-questions">
                <button
                  v-for="(q, idx) in quickQuestions"
                  :key="idx"
                  @click="sendMessage(q)"
                  class="quick-question-btn"
                >
                  {{ q }}
                </button>
              </div>
            </div>
          </div>

          <!-- 대화 메시지들 -->
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="message-wrapper"
            :class="msg.isUser ? 'user-message-wrapper' : 'ai-message-wrapper'"
          >
            <div class="message" :class="msg.isUser ? 'user-message' : 'ai-message'">
              <img v-if="!msg.isUser" :src="avatarImage" alt="AI" class="message-avatar" />
              <div class="message-content">
                <p v-html="formatMessage(msg.text)"></p>

                <!-- AI 추천 상품 카드 -->
                <div
                  v-if="!msg.isUser && msg.recommendedProducts && msg.recommendedProducts.length > 0"
                  class="recommended-products"
                >
                  <h6 class="products-title">추천 상품</h6>
                  <div
                    v-for="(product, pIdx) in msg.recommendedProducts"
                    :key="pIdx"
                    class="product-card"
                  >
                    <div class="product-info">
                      <span class="product-type-badge" :class="`badge-${product.type}`">
                        {{ getProductTypeLabel(product.type) }}
                      </span>
                      <p class="product-name">{{ product.name }}</p>
                      <p v-if="product.bank" class="product-bank">{{ product.bank }}</p>
                    </div>
                    <div class="product-actions">
                      <button
                        @click="toggleBookmark(product)"
                        class="bookmark-btn"
                        :class="{ 'bookmarked': isBookmarked(product.code) }"
                        :title="isBookmarked(product.code) ? '관심상품 해제' : '관심상품 추가'"
                      >
                        <span class="heart-icon">{{ isBookmarked(product.code) ? '❤️' : '🤍' }}</span>
                      </button>
                      <button
                        @click="viewProductDetail(product)"
                        class="detail-btn"
                      >
                        상세보기 →
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <span class="message-time">{{ msg.time }}</span>
            </div>
          </div>

          <!-- 로딩 인디케이터 -->
          <div v-if="isLoading" class="message-wrapper ai-message-wrapper">
            <div class="message ai-message">
              <img :src="avatarImage" alt="AI" class="message-avatar" />
              <div class="message-content">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 입력 영역 -->
        <div class="chatbot-input-area">
          <div class="input-container">
            <textarea
              v-model="userInput"
              @keydown.enter.prevent="handleEnter"
              placeholder="메시지를 입력하세요..."
              class="message-input"
              rows="1"
              ref="messageInput"
            ></textarea>
            <button
              @click="sendUserMessage"
              :disabled="!userInput.trim() || isLoading"
              class="send-btn"
            >
              <span class="send-icon">➤</span>
            </button>
          </div>
          <div class="input-footer">
            <button @click="clearHistory" class="clear-btn">대화 내역 삭제</button>
            <span class="ai-disclaimer">AI 답변은 참고용입니다</span>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/api/axios'
import legoImage from '@/assets/main/icon/lego.png'

const router = useRouter()
const authStore = useAuthStore()

// 로컬 스토리지 키 (사용자별로 구분)
const getStorageKey = () => {
  const username = authStore.user?.username || 'guest'
  return `chatbot_messages_${username}`
}

// 로컬 스토리지에서 메시지 로드
const loadMessagesFromStorage = () => {
  try {
    const stored = localStorage.getItem(getStorageKey())
    return stored ? JSON.parse(stored) : []
  } catch (error) {
    console.error('메시지 로드 실패:', error)
    return []
  }
}

// 로컬 스토리지에 메시지 저장
const saveMessagesToStorage = (msgs) => {
  try {
    localStorage.setItem(getStorageKey(), JSON.stringify(msgs))
  } catch (error) {
    console.error('메시지 저장 실패:', error)
  }
}

// State
const isOpen = ref(false)
const isLoading = ref(false)
const userInput = ref('')
const messages = ref(loadMessagesFromStorage()) // 로컬 스토리지에서 초기화
const messagesContainer = ref(null)
const messageInput = ref(null)
const hasNewRecommendation = ref(false)
const chatContainer = ref(null)

// 리사이즈 관련 상태
const containerWidth = ref(450)
const containerHeight = ref(700)
const isResizing = ref(false)
const resizeDirection = ref(null)

// 챗봇 아바타 정보
const avatarType = ref('normal')
const riskType = ref(null)
const riskScore = ref(null)

// 북마크된 상품 (Set으로 관리)
const bookmarkedProducts = ref(new Set())

// 빠른 질문
const quickQuestions = [
  '안정적인 예금 상품 추천해주세요',
  '고수익 투자 상품이 궁금해요',
  '주식 투자 시작하려면 어떻게 해야 하나요?',
]

// Computed
const riskTypeLabel = computed(() => {
  const labels = {
    'Timid': '안정형',
    'Normal': '중립형',
    'Speculative': '공격형',
  }
  return labels[riskType.value] || '일반'
})

const avatarImage = computed(() => {
  return legoImage
})

const containerStyle = computed(() => ({
  width: `${containerWidth.value}px`,
  height: `${containerHeight.value}px`,
}))

// Methods
const toggleChat = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    // 채팅창을 열 때 메시지가 없으면 환영 메시지 표시, 있으면 유지
    nextTick(() => {
      messageInput.value?.focus()
      scrollToBottom()
    })
  }
}

const handleEnter = (e) => {
  if (!e.shiftKey) {
    sendUserMessage()
  }
}

const sendMessage = (text) => {
  userInput.value = text
  sendUserMessage()
}

const sendUserMessage = async () => {
  const message = userInput.value.trim()
  if (!message || isLoading.value) return

  // 사용자 메시지 추가
  messages.value.push({
    text: message,
    isUser: true,
    time: formatTime(new Date()),
  })

  // 로컬 스토리지에 저장
  saveMessagesToStorage(messages.value)

  userInput.value = ''
  isLoading.value = true
  scrollToBottom()

  try {
    const response = await api.post('/chatbot/chat/', { message })

    // AI 응답 추가
    messages.value.push({
      text: response.data.ai_response,
      isUser: false,
      time: formatTime(new Date()),
      recommendedProducts: response.data.recommended_products,
    })

    // 로컬 스토리지에 저장
    saveMessagesToStorage(messages.value)

    if (response.data.recommended_products?.length > 0) {
      hasNewRecommendation.value = true
    }

    scrollToBottom()
  } catch (error) {
    console.error('챗봇 오류:', error)
    messages.value.push({
      text: '죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
      isUser: false,
      time: formatTime(new Date()),
    })
  } finally {
    isLoading.value = false
  }
}

const loadChatHistory = async () => {
  // 이 함수는 더 이상 자동으로 호출되지 않습니다
  // 사용자가 명시적으로 요청할 때만 호출됩니다
  try {
    const response = await api.get('/chatbot/history/', { params: { limit: 20 } })
    messages.value = response.data.map((msg) => [
      {
        text: msg.user_message,
        isUser: true,
        time: formatTime(new Date(msg.created_at)),
      },
      {
        text: msg.ai_response,
        isUser: false,
        time: formatTime(new Date(msg.created_at)),
        recommendedProducts: msg.recommended_products,
      },
    ]).flat()
    scrollToBottom()
  } catch (error) {
    console.error('채팅 히스토리 로드 실패:', error)
  }
}

const clearHistory = async () => {
  if (!confirm('모든 대화 내역을 삭제하시겠습니까?')) return

  try {
    await api.delete('/chatbot/history/')
    messages.value = []
    // 로컬 스토리지도 삭제
    localStorage.removeItem(getStorageKey())
    alert('대화 내역이 삭제되었습니다.')
  } catch (error) {
    console.error('대화 삭제 실패:', error)
    alert('대화 내역 삭제에 실패했습니다.')
  }
}

const fetchAvatarInfo = async () => {
  try {
    const response = await api.get('/chatbot/avatar/')
    avatarType.value = response.data.avatar || 'normal'
    riskType.value = response.data.risk_type
    riskScore.value = response.data.risk_score
  } catch (error) {
    console.error('아바타 정보 로드 실패:', error)
    avatarType.value = 'normal'
  }
}

const fetchBookmarks = async () => {
  try {
    const response = await api.get('/accounts/bookmarks/')
    bookmarkedProducts.value = new Set(response.data.map((b) => b.fin_prdt_cd))
  } catch (error) {
    console.error('북마크 로드 실패:', error)
  }
}

const toggleBookmark = async (product) => {
  try {
    await api.post(`/accounts/recommendations/${product.code}/bookmark/`)

    if (bookmarkedProducts.value.has(product.code)) {
      bookmarkedProducts.value.delete(product.code)
    } else {
      bookmarkedProducts.value.add(product.code)
    }
  } catch (error) {
    console.error('북마크 토글 실패:', error)
    alert('관심상품 등록에 실패했습니다.')
  }
}

const isBookmarked = (code) => {
  return bookmarkedProducts.value.has(code)
}

const viewProductDetail = (product) => {
  if (product.type === 'deposit') {
    router.push(`/finances/deposits/${product.code}`)
  } else if (product.type === 'saving') {
    router.push(`/finances/savings/${product.code}`)
  } else if (product.type === 'stock') {
    router.push(`/stocks/${product.code}`)
  }
  isOpen.value = false
}

const getProductTypeLabel = (type) => {
  const labels = {
    'deposit': '예금',
    'saving': '적금',
    'stock': '주식',
  }
  return labels[type] || '상품'
}

const formatMessage = (text) => {
  return text.replace(/\n/g, '<br>')
}

const formatTime = (date) => {
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const handleImageError = (e) => {
  // 이미지 로드 실패 시 기본 아이콘 표시
  e.target.style.display = 'none'
  e.target.parentElement.style.background = 'linear-gradient(135deg, #3b82f6 0%, #10b981 100%)'
  e.target.parentElement.innerHTML = '<span style="color: white; font-size: 32px;">🤖</span>'
}

// 리사이즈 함수
const startResize = (direction, e) => {
  e.preventDefault()
  isResizing.value = true
  resizeDirection.value = direction

  const startX = e.clientX
  const startY = e.clientY
  const startWidth = containerWidth.value
  const startHeight = containerHeight.value

  const handleMouseMove = (moveEvent) => {
    if (!isResizing.value) return

    const deltaX = startX - moveEvent.clientX
    const deltaY = startY - moveEvent.clientY

    if (direction.includes('left')) {
      const newWidth = startWidth + deltaX
      if (newWidth >= 350 && newWidth <= 800) {
        containerWidth.value = newWidth
      }
    }

    if (direction.includes('top')) {
      const newHeight = startHeight + deltaY
      if (newHeight >= 400 && newHeight <= 900) {
        containerHeight.value = newHeight
      }
    }
  }

  const handleMouseUp = () => {
    isResizing.value = false
    resizeDirection.value = null
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

// Lifecycle
onMounted(() => {
  if (authStore.isLogin) {
    fetchAvatarInfo()
    fetchBookmarks()
  }
})

watch(() => authStore.isLogin, (newVal) => {
  if (newVal) {
    // 로그인 시
    fetchAvatarInfo()
    fetchBookmarks()
    // 로그인한 사용자의 메시지 로드
    messages.value = loadMessagesFromStorage()
  } else {
    // 로그아웃 시 모든 상태 초기화
    messages.value = []
    isOpen.value = false
    avatarType.value = 'normal'
    riskType.value = null
    riskScore.value = null
    bookmarkedProducts.value = new Set()
    hasNewRecommendation.value = false
    // 로그아웃 시에는 로컬 스토리지에서 메시지를 삭제하지 않음 (다음 로그인 시 복원 가능)
  }
})
</script>

<style scoped>
.chatbot-widget {
  position: fixed;
  bottom: 30px;
  right: 30px;
  z-index: 9999;
}

/* 플로팅 버튼 */
.chatbot-floating-btn {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
  border: none;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  position: relative;
}

.chatbot-floating-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 12px 32px rgba(59, 130, 246, 0.5);
}

.chatbot-floating-btn.pulse {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
  }
  50% {
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.7);
  }
}

.chatbot-avatar-icon {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  object-fit: cover;
}

.notification-badge {
  position: absolute;
  top: 5px;
  right: 5px;
  background: #ff4757;
  color: white;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

/* 채팅 창 */
.chatbot-container {
  position: relative;
  background: white;
  border-radius: 20px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 350px;
  min-height: 400px;
  max-width: 800px;
  max-height: 900px;
}

/* 리사이즈 핸들 */
.resize-handle {
  position: absolute;
  z-index: 10;
}

.resize-handle-top {
  top: 0;
  left: 0;
  right: 0;
  height: 5px;
  cursor: ns-resize;
}

.resize-handle-left {
  left: 0;
  top: 0;
  bottom: 0;
  width: 5px;
  cursor: ew-resize;
}

.resize-handle-top-left {
  top: 0;
  left: 0;
  width: 15px;
  height: 15px;
  cursor: nwse-resize;
  background: transparent;
}

/* 헤더 */
.chatbot-header {
  background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chatbot-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: 3px solid rgba(255, 255, 255, 0.3);
  object-fit: cover;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.chatbot-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.chatbot-subtitle {
  margin: 4px 0 0 0;
  font-size: 13px;
  opacity: 0.9;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 32px;
  cursor: pointer;
  line-height: 1;
  transition: transform 0.2s;
}

.close-btn:hover {
  transform: rotate(90deg);
}

/* 메시지 영역 */
.chatbot-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f7f9fc;
}

.welcome-message {
  text-align: center;
  padding: 40px 20px;
}

.welcome-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  margin-bottom: 16px;
}

.welcome-text h5 {
  margin: 0 0 8px 0;
  color: #2c3e50;
  font-size: 18px;
}

.welcome-text p {
  margin: 0 0 20px 0;
  color: #6c757d;
  font-size: 14px;
}

.quick-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
}

.quick-question-btn {
  padding: 12px 16px;
  background: white;
  border: 1px solid #e0e6ed;
  border-radius: 12px;
  font-size: 13px;
  color: #495057;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.quick-question-btn:hover {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
  transform: translateY(-2px);
}

.message-wrapper {
  margin-bottom: 16px;
  display: flex;
}

.user-message-wrapper {
  justify-content: flex-end;
}

.ai-message-wrapper {
  justify-content: flex-start;
}

.message {
  max-width: 75%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  margin-right: 8px;
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
}

.user-message .message-content {
  background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-message {
  flex-direction: row;
  align-items: flex-start;
}

.ai-message .message-content {
  background: white;
  color: #2c3e50;
  border: 1px solid #e0e6ed;
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 11px;
  color: #95a5a6;
  margin-top: 4px;
  align-self: flex-end;
}

/* 추천 상품 */
.recommended-products {
  margin-top: 12px;
}

.products-title {
  font-size: 13px;
  font-weight: 600;
  color: #3b82f6;
  margin: 0 0 8px 0;
}

.product-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid #e9ecef;
}

.product-info {
  margin-bottom: 10px;
}

.product-type-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 6px;
}

.badge-deposit {
  background: #e3f2fd;
  color: #1976d2;
}

.badge-saving {
  background: #dcfce7;
  color: #16a34a;
}

.badge-stock {
  background: #fff3e0;
  color: #f57c00;
}

.product-name {
  margin: 4px 0;
  font-size: 13px;
  font-weight: 600;
  color: #2c3e50;
}

.product-bank {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #6c757d;
}

.product-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.bookmark-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 20px;
  transition: transform 0.2s;
  padding: 4px 8px;
}

.bookmark-btn:hover {
  transform: scale(1.2);
}

.detail-btn {
  flex: 1;
  padding: 8px 12px;
  background: white;
  border: 1px solid #3b82f6;
  border-radius: 8px;
  color: #3b82f6;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.detail-btn:hover {
  background: #3b82f6;
  color: white;
}

/* 타이핑 인디케이터 */
.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #95a5a6;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

/* 입력 영역 */
.chatbot-input-area {
  padding: 16px;
  background: white;
  border-top: 1px solid #e0e6ed;
}

.input-container {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  margin-bottom: 8px;
}

.message-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e0e6ed;
  border-radius: 24px;
  font-size: 14px;
  resize: none;
  max-height: 100px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.message-input:focus {
  border-color: #3b82f6;
}

.send-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.1);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.clear-btn {
  background: none;
  border: none;
  color: #6c757d;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
}

.clear-btn:hover {
  color: #495057;
}

.ai-disclaimer {
  font-size: 11px;
  color: #95a5a6;
}

/* Transitions */
.bounce-enter-active {
  animation: bounce-in 0.5s;
}

.bounce-leave-active {
  animation: bounce-out 0.3s;
}

@keyframes bounce-in {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes bounce-out {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(0);
    opacity: 0;
  }
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(100px);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(100px);
  opacity: 0;
}

/* Responsive */
@media (max-width: 480px) {
  .chatbot-container {
    width: calc(100vw - 32px);
    height: calc(100vh - 100px);
  }
}
</style>
