import { ref } from 'vue'

export function useAlert() {
  const showAlert = ref(false)
  const alertConfig = ref({
    icon: 'ℹ️',
    title: '알림',
    message: '',
    confirmText: '확인',
    cancelText: '취소',
    showCancel: false,
    hint: '',
    onConfirm: () => {},
    onCancel: () => {}
  })

  const alert = (message, options = {}) => {
    alertConfig.value = {
      icon: options.icon || 'ℹ️',
      title: options.title || '알림',
      message,
      confirmText: options.confirmText || '확인',
      cancelText: options.cancelText || '취소',
      showCancel: options.showCancel || false,
      hint: options.hint || '',
      onConfirm: options.onConfirm || (() => {}),
      onCancel: options.onCancel || (() => {})
    }
    showAlert.value = true
  }

  const confirm = (message, options = {}) => {
    return new Promise((resolve) => {
      alertConfig.value = {
        icon: options.icon || '❓',
        title: options.title || '확인',
        message,
        confirmText: options.confirmText || '확인',
        cancelText: options.cancelText || '취소',
        showCancel: true,
        hint: options.hint || '',
        onConfirm: () => {
          if (options.onConfirm) options.onConfirm()
          resolve(true)
        },
        onCancel: () => {
          if (options.onCancel) options.onCancel()
          resolve(false)
        }
      }
      showAlert.value = true
    })
  }

  const success = (message, options = {}) => {
    alert(message, { icon: '✅', title: '성공', ...options })
  }

  const error = (message, options = {}) => {
    alert(message, { icon: '⚠️', title: '오류', ...options })
  }

  const warning = (message, options = {}) => {
    alert(message, { icon: '⚠️', title: '경고', ...options })
  }

  const info = (message, options = {}) => {
    alert(message, { icon: 'ℹ️', title: '안내', ...options })
  }

  return {
    showAlert,
    alertConfig,
    alert,
    confirm,
    success,
    error,
    warning,
    info
  }
}
