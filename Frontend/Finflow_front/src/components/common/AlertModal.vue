<template>
  <transition name="modal-fade">
    <div v-if="modelValue" class="alert-modal-overlay" @click="handleClose">
      <div class="alert-modal" @click.stop>
        <div class="modal-icon">{{ icon }}</div>
        <h3 class="modal-title">{{ title }}</h3>
        <p class="modal-message" v-html="message"></p>

        <!-- 버튼이 1개인 경우 (확인만) -->
        <div v-if="!showCancel" class="modal-buttons single">
          <button @click="handleConfirm" class="btn-confirm">
            {{ confirmText }}
          </button>
        </div>

        <!-- 버튼이 2개인 경우 (확인 + 취소) -->
        <div v-else class="modal-buttons">
          <button @click="handleConfirm" class="btn-allow">
            {{ confirmText }}
          </button>
          <button @click="handleClose" class="btn-deny">
            {{ cancelText }}
          </button>
        </div>

        <p v-if="hint" class="modal-hint">
          {{ hint }}
        </p>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  icon: {
    type: String,
    default: 'ℹ️'
  },
  title: {
    type: String,
    default: '알림'
  },
  message: {
    type: String,
    required: true
  },
  confirmText: {
    type: String,
    default: '확인'
  },
  cancelText: {
    type: String,
    default: '취소'
  },
  showCancel: {
    type: Boolean,
    default: false
  },
  hint: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const handleClose = () => {
  emit('update:modelValue', false)
  emit('cancel')
}

const handleConfirm = () => {
  emit('update:modelValue', false)
  emit('confirm')
}
</script>

<style scoped>
.alert-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(4px);
}

.alert-modal {
  background: white;
  border-radius: 20px;
  padding: 36px 32px;
  max-width: 420px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  text-align: center;
  animation: modalSlideUp 0.3s ease-out;
}

@keyframes modalSlideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-icon {
  font-size: 64px;
  margin-bottom: 20px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.modal-title {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 16px;
}

.modal-message {
  font-size: 16px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 28px;
  white-space: pre-line;
}

.modal-buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.modal-buttons.single {
  justify-content: center;
}

.modal-buttons.single .btn-confirm {
  min-width: 120px;
}

.btn-allow,
.btn-confirm {
  flex: 1;
  padding: 14px 24px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transition: all 0.3s ease;
}

.btn-allow:hover,
.btn-confirm:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.btn-deny {
  flex: 1;
  padding: 14px 24px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  background: white;
  color: #666;
  transition: all 0.3s ease;
}

.btn-deny:hover {
  background: #f5f5f5;
  border-color: #ccc;
}

.modal-hint {
  font-size: 13px;
  color: #999;
  margin: 0;
}

/* 페이드 애니메이션 */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
