<script setup>
import { ref, computed, watch } from 'vue'
import AppInput from '../ui/AppInput.vue'
import AppSelect from '../ui/AppSelect.vue'
import AppButton from '../ui/AppButton.vue'
import AppModal from '../ui/AppModal.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  specialties: {
    type: Array,
    default: () => []
  },
  selectedSpecialtyId: {
    type: [Number, String],
    default: null
  },
  student: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'submit'])

const form = ref({
  last_name: '',
  first_name: '',
  middle_name: '',
  certificate_number: '',
  specialty_id: ''
})
const errors = ref({})
const loading = ref(false)
const serverError = ref('')

const specialtyOptions = ref([])

const isEdit = computed(() => !!props.student)

watch(() => props.show, (newVal) => {
  if (newVal) {
    if (props.student) {
      form.value = {
        last_name: props.student.last_name || '',
        first_name: props.student.first_name || '',
        middle_name: props.student.middle_name || '',
        certificate_number: props.student.certificate_number || '',
        specialty_id: props.student.specialty_id || ''
      }
    } else {
      form.value = {
        last_name: '',
        first_name: '',
        middle_name: '',
        certificate_number: '',
        specialty_id: props.selectedSpecialtyId || ''
      }
    }
    errors.value = {}
    serverError.value = ''
    specialtyOptions.value = props.specialties.map(s => ({
      value: s.id,
      label: `${s.code} - ${s.name}`
    }))
  }
})

function validate() {
  errors.value = {}
  if (!form.value.last_name.trim()) {
    errors.value.last_name = 'Введите фамилию'
  }
  if (!form.value.first_name.trim()) {
    errors.value.first_name = 'Введите имя'
  }
  if (!form.value.certificate_number.trim()) {
    errors.value.certificate_number = 'Введите номер аттестата'
  } else if (!/^\d+$/.test(form.value.certificate_number.trim())) {
    errors.value.certificate_number = 'Номер аттестата должен содержать только цифры'
  }
  if (!form.value.specialty_id) {
    errors.value.specialty_id = 'Выберите направление'
  }
  return Object.keys(errors.value).length === 0
}

async function submit() {
  if (!validate()) return

  loading.value = true
  serverError.value = ''

  try {
    await emit('submit', {
      last_name: form.value.last_name,
      first_name: form.value.first_name,
      middle_name: form.value.middle_name || null,
      certificate_number: form.value.certificate_number,
      specialty_id: Number(form.value.specialty_id)
    })
  } catch (error) {
    if (error.response?.data?.detail) {
      serverError.value = error.response.data.detail
    } else {
      serverError.value = isEdit.value ? 'Произошла ошибка при обновлении студента' : 'Произошла ошибка при добавлении студента'
    }
  } finally {
    loading.value = false
  }
}

function setError(message) {
  serverError.value = message
}

defineExpose({ setError })
</script>

<template>
  <AppModal
    :show="show"
    :title="isEdit ? 'Редактирование студента' : 'Новый студент'"
    @close="$emit('close')"
  >
    <form class="form" @submit.prevent="submit">
      <div v-if="serverError" class="server-error">
        {{ serverError }}
      </div>

      <AppInput
        v-model="form.last_name"
        label="Фамилия"
        placeholder="Введите фамилию"
        :error="errors.last_name"
        required
      />
      <AppInput
        v-model="form.first_name"
        label="Имя"
        placeholder="Введите имя"
        :error="errors.first_name"
        required
      />
      <AppInput
        v-model="form.middle_name"
        label="Отчество"
        placeholder="Введите отчество (необязательно)"
      />
      <AppInput
        v-model="form.certificate_number"
        label="Номер аттестата"
        placeholder="Введите номер аттестата"
        :error="errors.certificate_number"
        required
      />
      <AppSelect
        v-model="form.specialty_id"
        label="Направление"
        :options="specialtyOptions"
        :error="errors.specialty_id"
        required
      />
    </form>

    <template #footer>
      <AppButton variant="secondary" @click="$emit('close')">
        Отмена
      </AppButton>
      <AppButton :loading="loading" @click="submit">
        {{ isEdit ? 'Сохранить' : 'Добавить' }}
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

.server-error {
  padding: 12px;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #dc2626;
  font-size: 14px;
}
</style>
