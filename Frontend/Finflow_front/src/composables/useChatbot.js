// src/composables/useChatbot.js
import { ref } from 'vue'

// 전역 상태로 챗봇 열기 요청 관리
const chatbotOpenRequested = ref(false)

export function useChatbot() {
  const requestOpenChatbot = () => {
    chatbotOpenRequested.value = true
    // 즉시 리셋 (다음 프레임에서)
    setTimeout(() => {
      chatbotOpenRequested.value = false
    }, 100)
  }

  return {
    chatbotOpenRequested,
    requestOpenChatbot
  }
}
