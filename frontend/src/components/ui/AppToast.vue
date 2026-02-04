<script setup>
import { useToastStore } from '../../stores/toast'

const toastStore = useToastStore()

function getIcon(type) {
  switch (type) {
    case 'success':
      return '\u2713'
    case 'error':
      return '\u2717'
    case 'warning':
      return '\u26A0'
    default:
      return '\u2139'
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toastStore.toasts"
          :key="toast.id"
          :class="['toast', `toast--${toast.type}`]"
        >
          <span class="toast-icon">{{ getIcon(toast.type) }}</span>
          <span class="toast-message">{{ toast.message }}</span>
          <button class="toast-close" @click="toastStore.remove(toast.id)">
            &times;
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 400px;
}

.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  font-size: 14px;
  line-height: 1.4;
}

.toast--success {
  background: #ecfdf5;
  border-left: 4px solid #10b981;
  color: #065f46;
}

.toast--error {
  background: #fef2f2;
  border-left: 4px solid #ef4444;
  color: #991b1b;
}

.toast--warning {
  background: #fffbeb;
  border-left: 4px solid #f59e0b;
  color: #92400e;
}

.toast--info {
  background: #eff6ff;
  border-left: 4px solid #3b82f6;
  color: #1e40af;
}

.toast-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.toast-message {
  flex: 1;
}

.toast-close {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  opacity: 0.5;
  padding: 0;
  line-height: 1;
  flex-shrink: 0;
}

.toast-close:hover {
  opacity: 1;
}

/* Transition animations */
.toast-enter-active {
  animation: toast-in 0.3s ease-out;
}

.toast-leave-active {
  animation: toast-out 0.2s ease-in;
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes toast-out {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(100%);
  }
}
</style>
