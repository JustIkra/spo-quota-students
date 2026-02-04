<script setup>
import { ref, watch } from 'vue'
import AppInput from '../ui/AppInput.vue'
import AppButton from '../ui/AppButton.vue'
import AppModal from '../ui/AppModal.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  spo: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'submit'])

const form = ref({
  name: ''
})
const errors = ref({})
const loading = ref(false)

watch(() => props.show, (newVal) => {
  if (newVal) {
    if (props.spo) {
      form.value = { name: props.spo.name }
    } else {
      form.value = { name: '' }
    }
    errors.value = {}
  }
})

function validate() {
  errors.value = {}
  if (!form.value.name.trim()) {
    errors.value.name = 'Введите название СПО'
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
    :title="spo ? 'Редактирование СПО' : 'Новое СПО'"
    @close="$emit('close')"
  >
    <form @submit.prevent="submit">
      <AppInput
        v-model="form.name"
        label="Название СПО"
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
        {{ spo ? 'Сохранить' : 'Создать' }}
      </AppButton>
    </template>
  </AppModal>
</template>
