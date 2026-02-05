<script setup>
import { ref, watch } from 'vue'
import AppInput from '../ui/AppInput.vue'
import AppButton from '../ui/AppButton.vue'
import AppModal from '../ui/AppModal.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'submit'])

const form = ref({
  code: '',
  name: ''
})
const errors = ref({})
const loading = ref(false)

watch(() => props.show, (newVal) => {
  if (newVal) {
    form.value = { code: '', name: '' }
    errors.value = {}
  }
})

function validate() {
  errors.value = {}
  if (!form.value.code.trim()) {
    errors.value.code = 'Введите код направления'
  }
  if (!form.value.name.trim()) {
    errors.value.name = 'Введите название направления'
  }
  return Object.keys(errors.value).length === 0
}

async function submit() {
  if (!validate()) return

  loading.value = true
  try {
    await emit('submit', { ...form.value })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AppModal
    :show="show"
    title="Новая направление"
    @close="$emit('close')"
  >
    <form class="form" @submit.prevent="submit">
      <AppInput
        v-model="form.code"
        label="Код направления"
        placeholder="Например: 09.02.07"
        :error="errors.code"
        required
      />
      <AppInput
        v-model="form.name"
        label="Название"
        placeholder="Введите название"
        :error="errors.name"
        required
      />
    </form>

    <template #footer>
      <AppButton variant="secondary" @click="$emit('close')">
        Отмена
      </AppButton>
      <AppButton :loading="loading" @click="submit">
        Добавить
      </AppButton>
    </template>
  </AppModal>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
