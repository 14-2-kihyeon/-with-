// src/composables/useChatbot.js
import { ref } from 'vue'

// 전역 상태로 챗봇 열기 요청 관리
const chatbotOpenRequested = ref(false)

// 전역 상태로 챗봇 아바타 새로고침 요청 관리
const chatbotAvatarRefreshRequested = ref(0)

export function useChatbot() {
  const requestOpenChatbot = () => {
    chatbotOpenRequested.value = true
    // 즉시 리셋 (다음 프레임에서)
    setTimeout(() => {
      chatbotOpenRequested.value = false
    }, 100)
  }

  const requestRefreshAvatar = () => {
    // 값을 증가시켜서 watch가 감지할 수 있도록 함
    chatbotAvatarRefreshRequested.value++
  }

  return {
    chatbotOpenRequested,
    chatbotAvatarRefreshRequested,
    requestOpenChatbot,
    requestRefreshAvatar
  }
}
