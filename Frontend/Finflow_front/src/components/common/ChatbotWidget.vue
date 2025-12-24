<template>
  <div class="chatbot-widget" :class="{ 'dragging': isDragging }" :style="widgetPositionStyle">
    <!-- 로그인 안내 말풍선 -->
    <transition name="fade">
      <div v-if="showLoginTooltip" class="login-tooltip">
        <button @click="closeTooltip" class="tooltip-close-btn">&times;</button>
        <div class="tooltip-content">
          <div class="tooltip-icon">🔒</div>
          <h4 class="tooltip-title">로그인이 필요합니다</h4>
          <p class="tooltip-message">AI 챗봇을 사용하려면<br>로그인이 필요해요</p>
          <button @click="goToLogin" class="tooltip-login-btn">
            로그인하러 가기 →
          </button>
        </div>
      </div>
    </transition>

    <!-- 플로팅 버튼 -->
    <transition name="bounce">
      <button
        v-if="!isOpen"
        @click="handleWidgetClick"
        @mousedown="startDrag"
        class="chatbot-floating-btn"
        :class="{ 'pulse': hasNewRecommendation, 'dragging': isDragging }"
      >
        <img :src="widgetImage" alt="AI 챗봇" class="chatbot-avatar-icon" @error="handleImageError" />
        <span v-if="hasNewRecommendation" class="notification-badge">!</span>
      </button>
    </transition>

    <!-- 채팅 창 -->
    <transition name="slide-up">
      <div v-if="isOpen" class="chatbot-container" ref="chatContainer" :style="chatContainerStyle">
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
              <div class="message-bubble">
                <div v-if="!msg.isUser" class="ai-name">Finflow AI</div>
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
          </div>

          <!-- 로딩 인디케이터 -->
          <div v-if="isLoading" class="message-wrapper ai-message-wrapper">
            <div class="message ai-message">
              <img :src="avatarImage" alt="AI" class="message-avatar" />
              <div class="message-bubble">
                <div class="ai-name">Finflow AI</div>
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

// 드래그 관련 상태
const isDragging = ref(false)
const dragPosition = ref(loadDragPosition())
const wasRecentlyDragging = ref(false)

// 위젯 위치 로드/저장 (픽셀 단위)
function loadDragPosition() {
  const saved = localStorage.getItem('chatbot_widget_drag_position')
  if (saved) {
    return JSON.parse(saved)
  }
  // 기본값: 오른쪽 하단
  return { bottom: 30, right: 30, top: null, left: null }
}

function saveDragPosition(position) {
  localStorage.setItem('chatbot_widget_drag_position', JSON.stringify(position))
}

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



// 성향별 챗봇 이미지 설정 (public/assets/chatbot/ 폴더에 아래 이미지 파일들을 추가하세요)
const CHATBOT_IMAGES = {
  // 위젯 버튼용 이미지 (플로팅 버튼에 표시)
  widget: {
    'guest': '/assets/chatbot/guest-widget.png',        // 비로그인 사용자용 위젯 이미지
    'timid': '/assets/chatbot/timid-widget.png',        // 안정형 위젯 이미지
    'normal': '/assets/chatbot/normal-widget.png',      // 중립형 위젯 이미지
    'speculative': '/assets/chatbot/speculative-widget.png',  // 공격형 위젯 이미지
  },
  // 프로필/아바타용 이미지 (헤더와 메시지에 표시)
  profile: {
    'guest': '/assets/chatbot/guest-profile.png',       // 비로그인 사용자용 프로필 이미지
    'timid': '/assets/chatbot/timid-profile.png',       // 안정형 프로필 이미지
    'normal': '/assets/chatbot/normal-profile.png',     // 중립형 프로필 이미지
    'speculative': '/assets/chatbot/speculative-profile.png',  // 공격형 프로필 이미지
  }
}

const avatarImage = computed(() => {
  // 비로그인 상태면 게스트 이미지 사용 (없으면 normal)
  if (!authStore.isLogin) {
    return CHATBOT_IMAGES.profile.guest || CHATBOT_IMAGES.profile.normal
  }
  // 프로필 이미지 반환 (헤더, 메시지, 환영 메시지용)
  const image = CHATBOT_IMAGES.profile[avatarType.value]
  console.log('avatarImage:', avatarType.value, '→', image)
  return image || CHATBOT_IMAGES.profile.normal
})

const widgetImage = computed(() => {
  // 비로그인 상태면 게스트 이미지 사용 (없으면 normal)
  if (!authStore.isLogin) {
    return CHATBOT_IMAGES.widget.guest || CHATBOT_IMAGES.widget.normal
  }
  // 위젯 버튼 이미지 반환 (플로팅 버튼용)
  const image = CHATBOT_IMAGES.widget[avatarType.value]
  console.log('widgetImage:', avatarType.value, '→', image)
  return image || CHATBOT_IMAGES.widget.normal
})

const chatContainerStyle = computed(() => {
  const pos = dragPosition.value
  const style = {
    width: `${containerWidth.value}px`,
    height: `${containerHeight.value}px`,
  }

  // navbar 높이 (일반적으로 60-80px, 여유있게 100px로 설정)
  const navbarHeight = 100
  const margin = 30
  const chatWidth = containerWidth.value
  const chatHeight = containerHeight.value
  const widgetSize = 70

  // 위젯의 실제 픽셀 위치 계산
  let widgetX, widgetY

  if (pos.left !== null) {
    widgetX = pos.left
  } else {
    widgetX = window.innerWidth - pos.right - widgetSize
  }

  if (pos.top !== null) {
    widgetY = pos.top
  } else {
    widgetY = window.innerHeight - pos.bottom - widgetSize
  }

  // 가로축: 위젯의 위치에 맞춰 채팅창 배치 (화면 경계 고려)
  let chatX = widgetX

  // 채팅창이 화면 오른쪽을 넘어가는지 체크
  if (chatX + chatWidth > window.innerWidth - margin) {
    // 화면 오른쪽을 넘어가면 오른쪽에 맞춤
    style.right = `${margin}px`
    style.left = 'auto'
  } else if (chatX < margin) {
    // 화면 왼쪽을 넘어가면 왼쪽에 맞춤
    style.left = `${margin}px`
    style.right = 'auto'
  } else {
    // 정상 범위 내에 있으면 위젯의 가로 위치에 맞춤
    style.left = `${chatX}px`
    style.right = 'auto'
  }

  // 세로축: navbar와 화면 하단 고려
  const minTop = navbarHeight + margin
  let chatY = widgetY

  // 채팅창이 화면 아래를 넘어가는지 체크
  if (chatY + chatHeight > window.innerHeight - margin) {
    // 화면 아래를 넘어가면 화면 하단에 맞춤
    style.bottom = `${margin}px`
    style.top = 'auto'
  } else if (chatY < minTop) {
    // navbar와 겹치면 navbar 아래로 배치
    style.top = `${minTop}px`
    style.bottom = 'auto'
  } else {
    // 정상 범위 내에 있으면 위젯의 세로 위치에 맞춤
    style.top = `${chatY}px`
    style.bottom = 'auto'
  }

  return style
})

const widgetPositionStyle = computed(() => {
  const pos = dragPosition.value
  const style = {}

  if (pos.top !== null) {
    style.top = `${pos.top}px`
    style.bottom = 'auto'
  } else {
    style.bottom = `${pos.bottom}px`
    style.top = 'auto'
  }

  if (pos.left !== null) {
    style.left = `${pos.left}px`
    style.right = 'auto'
  } else {
    style.right = `${pos.right}px`
    style.left = 'auto'
  }

  return style
})

// 로그인 안내 말풍선 상태
const showLoginTooltip = ref(false)

// Methods
const handleWidgetClick = (e) => {
  // 드래그 직후라면 클릭 이벤트 무시
  if (wasRecentlyDragging.value) {
    e.preventDefault()
    e.stopPropagation()
    return
  }
  toggleChat()
}

const toggleChat = () => {
  // 로그인 상태 확인
  if (!authStore.isLogin) {
    // 비로그인 상태면 말풍선 표시
    showLoginTooltip.value = !showLoginTooltip.value
    return
  }

  isOpen.value = !isOpen.value
  if (isOpen.value) {
    // 채팅창을 열 때 메시지가 없으면 환영 메시지 표시, 있으면 유지
    nextTick(() => {
      messageInput.value?.focus()
      scrollToBottom()
    })
  }
}

const goToLogin = () => {
  showLoginTooltip.value = false
  router.push('/login')
}

const closeTooltip = () => {
  showLoginTooltip.value = false
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
    // 백엔드에서 받은 avatar 값을 소문자로 변환 (Timid -> timid)
    const avatarValue = response.data.avatar || 'normal'
    avatarType.value = avatarValue.toLowerCase()
    riskType.value = response.data.risk_type
    riskScore.value = response.data.risk_score

    console.log('아바타 정보 로드:', {
      avatar: avatarType.value,
      riskType: riskType.value,
      riskScore: riskScore.value
    })
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
  // 이미지 로드 실패 시 기본 아이콘 표시 (이모지로 대체)
  console.warn('이미지 로드 실패:', e.target.src)
  e.target.style.display = 'none'

  // 부모 요소에 이모지 아이콘 추가
  const parent = e.target.parentElement
  parent.style.display = 'flex'
  parent.style.alignItems = 'center'
  parent.style.justifyContent = 'center'

  // 기존 내용 제거하고 이모지만 표시
  const emoji = document.createElement('span')
  emoji.style.fontSize = '40px'
  emoji.textContent = '🤖'

  parent.innerHTML = ''
  parent.appendChild(emoji)
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

// 드래그 함수
const startDrag = (e) => {
  const startX = e.clientX
  const startY = e.clientY
  const currentPos = { ...dragPosition.value }

  // 현재 위젯의 실제 위치 계산
  let widgetStartX, widgetStartY
  if (currentPos.left !== null) {
    widgetStartX = currentPos.left
  } else {
    widgetStartX = window.innerWidth - currentPos.right - 70 // 70은 위젯 크기
  }

  if (currentPos.top !== null) {
    widgetStartY = currentPos.top
  } else {
    widgetStartY = window.innerHeight - currentPos.bottom - 70
  }

  let hasMoved = false

  const handleMouseMove = (moveEvent) => {
    const deltaX = moveEvent.clientX - startX
    const deltaY = moveEvent.clientY - startY

    // 5px 이상 이동하면 드래그로 간주
    if (Math.abs(deltaX) > 5 || Math.abs(deltaY) > 5) {
      hasMoved = true
      isDragging.value = true

      // 새 위치 계산
      let newX = widgetStartX + deltaX
      let newY = widgetStartY + deltaY

      // 화면 경계 체크
      const maxX = window.innerWidth - 70
      const maxY = window.innerHeight - 70

      newX = Math.max(0, Math.min(newX, maxX))
      newY = Math.max(0, Math.min(newY, maxY))

      // 화면 중앙을 기준으로 어느 쪽에 가까운지 판단하여 위치 설정
      const centerX = window.innerWidth / 2
      const centerY = window.innerHeight / 2

      if (newX < centerX) {
        // 왼쪽
        dragPosition.value = {
          left: newX,
          right: null,
          top: newY < centerY ? newY : null,
          bottom: newY < centerY ? null : window.innerHeight - newY - 70
        }
      } else {
        // 오른쪽
        dragPosition.value = {
          left: null,
          right: window.innerWidth - newX - 70,
          top: newY < centerY ? newY : null,
          bottom: newY < centerY ? null : window.innerHeight - newY - 70
        }
      }
    }
  }

  const handleMouseUp = (upEvent) => {
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)

    if (hasMoved) {
      // 드래그가 발생했으면 현재 위치 저장하고 클릭 이벤트 방지
      e.preventDefault()
      upEvent.preventDefault()
      saveDragPosition(dragPosition.value)
      isDragging.value = false
      wasRecentlyDragging.value = true

      // 200ms 후 플래그 해제 (클릭 이벤트가 발생하지 않도록)
      setTimeout(() => {
        wasRecentlyDragging.value = false
      }, 200)
    } else {
      // 드래그가 아니면 일반 클릭으로 처리 (toggleChat이 자동으로 실행됨)
      isDragging.value = false
      wasRecentlyDragging.value = false
    }
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
  z-index: 9999;
}

.chatbot-widget:not(.dragging) {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 로그인 안내 말풍선 */
.login-tooltip {
  position: absolute;
  bottom: 90px;
  right: 0;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  padding: 24px;
  min-width: 280px;
  z-index: 10000;
}

.login-tooltip::after {
  content: '';
  position: absolute;
  bottom: -10px;
  right: 25px;
  width: 0;
  height: 0;
  border-left: 10px solid transparent;
  border-right: 10px solid transparent;
  border-top: 10px solid white;
}

.tooltip-close-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: none;
  border: none;
  font-size: 24px;
  color: #95a5a6;
  cursor: pointer;
  line-height: 1;
  padding: 4px;
  transition: color 0.2s;
}

.tooltip-close-btn:hover {
  color: #2c3e50;
}

.tooltip-content {
  text-align: center;
}

.tooltip-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.tooltip-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.tooltip-message {
  margin: 0 0 20px 0;
  font-size: 14px;
  color: #6c757d;
  line-height: 1.5;
}

.tooltip-login-btn {
  width: 100%;
  padding: 12px 24px;
  background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.tooltip-login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
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

.chatbot-floating-btn.dragging {
  cursor: grabbing;
  opacity: 0.8;
  transform: scale(1.05);
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
  position: fixed;
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
  z-index: 9998;
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
  padding: 24px 20px;
  background: linear-gradient(to bottom, #f8fafc 0%, #f1f5f9 100%);
}

.chatbot-messages::-webkit-scrollbar {
  width: 6px;
}

.chatbot-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chatbot-messages::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.chatbot-messages::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
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
  margin-bottom: 20px;
  display: flex;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message-wrapper {
  justify-content: flex-end;
}

.ai-message-wrapper {
  justify-content: flex-start;
}

.message {
  max-width: 80%;
  display: flex;
  gap: 8px;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-bubble {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.ai-name {
  font-size: 12px;
  font-weight: 600;
  color: #3b82f6;
  padding-left: 4px;
}

.message-content {
  padding: 14px 18px;
  border-radius: 18px;
  font-size: 15px;
  line-height: 1.6;
  word-wrap: break-word;
}

.message-content p {
  margin: 0;
  white-space: pre-wrap;
}

.user-message {
  flex-direction: row-reverse;
}

.user-message .message-bubble {
  align-items: flex-end;
}

.user-message .message-content {
  background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
  color: white;
  border-bottom-right-radius: 6px;
  box-shadow: 0 2px 12px rgba(59, 130, 246, 0.3);
}

.ai-message {
  flex-direction: row;
  align-items: flex-start;
}

.ai-message .message-content {
  background: white;
  color: #2c3e50;
  border: 1px solid #e0e6ed;
  border-bottom-left-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.message-time {
  font-size: 11px;
  color: #95a5a6;
  padding: 0 4px;
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

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
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
