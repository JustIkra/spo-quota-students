<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  options: {
    type: Array,
    default: () => []
    // [{ value: 1, label: 'Option 1' }]
  },
  label: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Выберите...'
  },
  error: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const selectRef = ref(null)
const controlRef = ref(null)
const dropdownRef = ref(null)
const highlightedIndex = ref(-1)
const dropdownStyle = ref({})

const selectedLabel = computed(() => {
  const option = props.options.find(opt => opt.value == props.modelValue)
  return option ? option.label : ''
})

function updateDropdownPosition() {
  if (!controlRef.value) return

  const rect = controlRef.value.getBoundingClientRect()
  const viewportHeight = window.innerHeight
  const spaceBelow = viewportHeight - rect.bottom - 20
  const maxHeight = Math.min(400, Math.max(200, spaceBelow))

  dropdownStyle.value = {
    position: 'fixed',
    top: `${rect.bottom + 4}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`,
    maxHeight: `${maxHeight}px`,
    zIndex: 9999
  }
}

function toggle() {
  if (props.disabled) return
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    highlightedIndex.value = props.options.findIndex(opt => opt.value == props.modelValue)
    nextTick(() => {
      updateDropdownPosition()
    })
  }
}

function close() {
  isOpen.value = false
  highlightedIndex.value = -1
}

function selectOption(option) {
  emit('update:modelValue', option.value)
  close()
}

function handleKeydown(e) {
  if (!isOpen.value) {
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
      e.preventDefault()
      isOpen.value = true
      highlightedIndex.value = Math.max(0, props.options.findIndex(opt => opt.value == props.modelValue))
      nextTick(() => updateDropdownPosition())
    }
    return
  }

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      highlightedIndex.value = Math.min(highlightedIndex.value + 1, props.options.length - 1)
      scrollToHighlighted()
      break
    case 'ArrowUp':
      e.preventDefault()
      highlightedIndex.value = Math.max(highlightedIndex.value - 1, 0)
      scrollToHighlighted()
      break
    case 'Enter':
      e.preventDefault()
      if (highlightedIndex.value >= 0 && props.options[highlightedIndex.value]) {
        selectOption(props.options[highlightedIndex.value])
      }
      break
    case 'Escape':
      e.preventDefault()
      close()
      break
  }
}

function scrollToHighlighted() {
  nextTick(() => {
    if (dropdownRef.value && highlightedIndex.value >= 0) {
      const options = dropdownRef.value.querySelectorAll('.select-option')
      if (options[highlightedIndex.value]) {
        options[highlightedIndex.value].scrollIntoView({ block: 'nearest' })
      }
    }
  })
}

function handleClickOutside(e) {
  if (selectRef.value && !selectRef.value.contains(e.target) &&
      dropdownRef.value && !dropdownRef.value.contains(e.target)) {
    close()
  }
}

function handleScroll() {
  if (isOpen.value) {
    updateDropdownPosition()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('scroll', handleScroll, true)
  window.addEventListener('resize', handleScroll)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('scroll', handleScroll, true)
  window.removeEventListener('resize', handleScroll)
})
</script>

<template>
  <div class="select-group" ref="selectRef">
    <label v-if="label" class="label">
      {{ label }}
      <span v-if="required" class="required">*</span>
    </label>
    <div
      ref="controlRef"
      class="select-control"
      :class="{
        'select-open': isOpen,
        'select-error': error,
        'select-disabled': disabled
      }"
      tabindex="0"
      @click="toggle"
      @keydown="handleKeydown"
    >
      <span class="select-value" :class="{ 'select-placeholder': !selectedLabel }">
        {{ selectedLabel || placeholder }}
      </span>
      <svg class="select-icon" :class="{ 'icon-rotated': isOpen }" width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M5 7.5L10 12.5L15 7.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>

    <Teleport to="body">
      <Transition name="dropdown">
        <div
          v-if="isOpen"
          ref="dropdownRef"
          class="select-dropdown"
          :style="dropdownStyle"
        >
          <div
            v-for="(option, index) in options"
            :key="option.value"
            class="select-option"
            :class="{
              'option-selected': option.value == modelValue,
              'option-highlighted': index === highlightedIndex
            }"
            @click.stop="selectOption(option)"
            @mouseenter="highlightedIndex = index"
          >
            <span class="option-text">{{ option.label }}</span>
            <svg v-if="option.value == modelValue" class="option-check" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M13.5 4.5L6.5 11.5L3 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div v-if="options.length === 0" class="select-empty">
            Нет доступных вариантов
          </div>
        </div>
      </Transition>
    </Teleport>

    <span v-if="error" class="error">{{ error }}</span>
  </div>
</template>

<style scoped>
.select-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
}

.label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.required {
  color: #dc2626;
  margin-left: 2px;
}

.select-control {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.5;
  color: #111827;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background-color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  outline: none;
  min-height: 42px;
}

.select-control:hover:not(.select-disabled) {
  border-color: #9ca3af;
  background-color: #fafafa;
}

.select-control:focus:not(.select-disabled) {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
  background-color: white;
}

.select-open {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
  background-color: white;
}

.select-disabled {
  background-color: #f3f4f6;
  color: #9ca3af;
  cursor: not-allowed;
}

.select-error {
  border-color: #dc2626;
}

.select-error:focus {
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.12);
}

.select-value {
  flex: 1;
  word-break: break-word;
}

.select-placeholder {
  color: #9ca3af;
}

.select-icon {
  flex-shrink: 0;
  color: #6b7280;
  transition: transform 0.2s ease, color 0.2s ease;
  margin-left: 8px;
  margin-top: 1px;
}

.icon-rotated {
  transform: rotate(180deg);
  color: #2563eb;
}

.error {
  font-size: 12px;
  color: #dc2626;
}
</style>

<style>
/* Global styles for teleported dropdown */
.select-dropdown {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 40px -5px rgba(0, 0, 0, 0.15), 0 8px 20px -6px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  overscroll-behavior: contain;
}

.select-option {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.5;
  color: #374151;
  cursor: pointer;
  transition: background-color 0.15s ease;
  gap: 12px;
  border-bottom: 1px solid #f3f4f6;
}

.select-option:first-child {
  border-radius: 7px 7px 0 0;
}

.select-option:last-child {
  border-radius: 0 0 7px 7px;
  border-bottom: none;
}

.select-option:only-child {
  border-radius: 7px;
  border-bottom: none;
}

.option-highlighted {
  background-color: #f3f4f6;
}

.option-selected {
  background-color: #eff6ff;
  color: #2563eb;
  font-weight: 500;
}

.option-selected.option-highlighted {
  background-color: #dbeafe;
}

.option-text {
  flex: 1;
  word-break: break-word;
}

.option-check {
  flex-shrink: 0;
  color: #2563eb;
  margin-top: 2px;
}

.select-empty {
  padding: 16px;
  text-align: center;
  color: #9ca3af;
  font-size: 14px;
}

/* Dropdown animation */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Scrollbar styling */
.select-dropdown::-webkit-scrollbar {
  width: 6px;
}

.select-dropdown::-webkit-scrollbar-track {
  background: transparent;
}

.select-dropdown::-webkit-scrollbar-thumb {
  background-color: #d1d5db;
  border-radius: 3px;
}

.select-dropdown::-webkit-scrollbar-thumb:hover {
  background-color: #9ca3af;
}
</style>
