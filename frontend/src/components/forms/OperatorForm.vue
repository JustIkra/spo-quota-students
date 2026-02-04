<script setup>
import { ref, watch } from 'vue'
import AppSelect from '../ui/AppSelect.vue'
import AppButton from '../ui/AppButton.vue'
import AppModal from '../ui/AppModal.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  spoList: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'submit'])

const form = ref({
  spo_id: ''
})
const errors = ref({})
const loading = ref(false)

const spoOptions = ref([])

watch(() => props.show, (newVal) => {
  if (newVal) {
    form.value = { spo_id: '' }
    errors.value = {}
    spoOptions.value = props.spoList.map(spo => ({
      value: spo.id,
      label: spo.name
    }))
  }
})

function validate() {
  errors.value = {}
  if (!form.value.spo_id) {
    errors.value.spo_id = 'Выберите учреждение'
  }
  return Object.keys(errors.value).length === 0
}

async function submit() {
  if (!validate()) return

  loading.value = true
  try {
    await emit('submit', {
      spo_id: Number(form.value.spo_id)
    })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AppModal
    :show="show"
    title="Новый оператор"
    @close="$emit('close')"
  >
    <form class="form" @submit.prevent="submit">
      <AppSelect
        v-model="form.spo_id"
        label="Учреждение"
        :options="spoOptions"
        :error="errors.spo_id"
        required
      />
    </form>

    <template #footer>
      <AppButton variant="secondary" @click="$emit('close')">
        Отмена
      </AppButton>
      <AppButton :loading="loading" @click="submit">
        Создать
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
