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
const noAvailableSpo = ref(false)

watch(() => props.show, (newVal) => {
  if (newVal) {
    form.value = { spo_id: '' }
    errors.value = {}
    // Filter SPOs that don't have operators (operators_count === 0)
    const available = props.spoList.filter(spo => spo.operators_count === 0)
    spoOptions.value = available.map(spo => ({
      value: spo.id,
      label: spo.name
    }))
    noAvailableSpo.value = available.length === 0
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
    <div v-if="noAvailableSpo" class="no-spo-warning">
      <p>Нет доступных учреждений для создания оператора.</p>
      <p class="hint">У каждого учреждения может быть только один оператор. Все учреждения уже имеют операторов.</p>
    </div>
    <form v-else class="form" @submit.prevent="submit">
      <p class="info-text">
        У каждого учреждения может быть только один оператор.
        Показаны только учреждения без оператора.
      </p>
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
        {{ noAvailableSpo ? 'Закрыть' : 'Отмена' }}
      </AppButton>
      <AppButton v-if="!noAvailableSpo" :loading="loading" @click="submit">
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

.info-text {
  color: #6b7280;
  font-size: 14px;
  padding: 12px;
  background: #f3f4f6;
  border-radius: 8px;
  margin: 0;
}

.no-spo-warning {
  text-align: center;
  padding: 20px;
}

.no-spo-warning p {
  margin: 0 0 8px 0;
}

.no-spo-warning .hint {
  color: #6b7280;
  font-size: 14px;
}
</style>
