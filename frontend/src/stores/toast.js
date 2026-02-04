import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])
  let nextId = 1

  function show(message, type = 'info', duration = 4000) {
    const id = nextId++
    toasts.value.push({ id, message, type })

    if (duration > 0) {
      setTimeout(() => {
        remove(id)
      }, duration)
    }

    return id
  }

  function success(message, duration = 4000) {
    return show(message, 'success', duration)
  }

  function error(message, duration = 5000) {
    return show(message, 'error', duration)
  }

  function warning(message, duration = 4000) {
    return show(message, 'warning', duration)
  }

  function info(message, duration = 4000) {
    return show(message, 'info', duration)
  }

  function remove(id) {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  return {
    toasts,
    show,
    success,
    error,
    warning,
    info,
    remove
  }
})
