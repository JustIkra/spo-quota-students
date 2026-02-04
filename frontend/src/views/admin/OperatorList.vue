<script setup>
import { ref, onMounted, computed } from 'vue'
import { adminApi } from '../../api/admin'
import { useToastStore } from '../../stores/toast'
import AppButton from '../../components/ui/AppButton.vue'
import AppTable from '../../components/ui/AppTable.vue'
import OperatorForm from '../../components/forms/OperatorForm.vue'
import AppModal from '../../components/ui/AppModal.vue'

const toast = useToastStore()

const operators = ref([])
const spoList = ref([])
const loading = ref(true)
const showForm = ref(false)
const showDeleteModal = ref(false)
const deletingOperator = ref(null)
const showPasswordModal = ref(false)
const showResetModal = ref(false)
const resettingOperator = ref(null)
const generatedPassword = ref('')
const createdLogin = ref('')
const isPasswordReset = ref(false)

const columns = [
  { key: 'id', label: 'ID', width: '80px' },
  { key: 'login', label: 'Логин' },
  { key: 'spo_name', label: 'СПО' },
  { key: 'created_at', label: 'Дата создания', width: '180px' },
  { key: 'actions', label: 'Действия', width: '240px' }
]

const operatorsWithSpo = computed(() => {
  return operators.value.map(op => ({
    ...op,
    spo_name: spoList.value.find(s => s.id === op.spo_id)?.name || '-'
  }))
})

onMounted(() => {
  loadData()
})

async function loadData() {
  loading.value = true
  try {
    const [ops, spos] = await Promise.all([
      adminApi.getOperators(),
      adminApi.getSpoList()
    ])
    operators.value = ops
    spoList.value = spos
  } catch (error) {
    console.error('Ошибка загрузки:', error)
  } finally {
    loading.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

async function handleSubmit(data) {
  try {
    const result = await adminApi.createOperator(data)
    showForm.value = false

    // Показываем сгенерированный пароль
    createdLogin.value = result.login
    generatedPassword.value = result.generated_password
    isPasswordReset.value = false
    showPasswordModal.value = true

    await loadData()
  } catch (error) {
    console.error('Ошибка создания:', error)
    toast.error('Ошибка создания: ' + (error.response?.data?.detail || 'Неизвестная ошибка'))
  }
}

function confirmDelete(operator) {
  deletingOperator.value = operator
  showDeleteModal.value = true
}

async function deleteOperator() {
  if (!deletingOperator.value) return

  try {
    await adminApi.deleteOperator(deletingOperator.value.id)
    showDeleteModal.value = false
    deletingOperator.value = null
    await loadData()
  } catch (error) {
    console.error('Ошибка удаления:', error)
    toast.error('Ошибка удаления: ' + (error.response?.data?.detail || 'Неизвестная ошибка'))
  }
}

function confirmResetPassword(operator) {
  resettingOperator.value = operator
  showResetModal.value = true
}

async function resetPassword() {
  if (!resettingOperator.value) return

  try {
    const result = await adminApi.resetOperatorPassword(resettingOperator.value.id)
    showResetModal.value = false

    // Show new password
    createdLogin.value = result.login
    generatedPassword.value = result.generated_password
    isPasswordReset.value = true
    showPasswordModal.value = true

    resettingOperator.value = null
  } catch (error) {
    console.error('Ошибка сброса пароля:', error)
    toast.error('Ошибка сброса пароля: ' + (error.response?.data?.detail || 'Неизвестная ошибка'))
  }
}

function copyPassword() {
  navigator.clipboard.writeText(generatedPassword.value)
  toast.success('Пароль скопирован в буфер обмена')
}
</script>

<template>
  <div class="operator-list">
    <div class="page-header">
      <h1 class="page-title">Список операторов</h1>
      <AppButton @click="showForm = true">Добавить оператора</AppButton>
    </div>

    <AppTable
      :columns="columns"
      :data="operatorsWithSpo"
      :loading="loading"
      empty-text="Нет зарегистрированных операторов"
    >
      <template #created_at="{ value }">
        {{ formatDate(value) }}
      </template>
      <template #actions="{ row }">
        <div class="action-buttons">
          <AppButton variant="secondary" @click="confirmResetPassword(row)">
            Сбросить пароль
          </AppButton>
          <AppButton variant="danger" @click="confirmDelete(row)">
            Удалить
          </AppButton>
        </div>
      </template>
    </AppTable>

    <OperatorForm
      :show="showForm"
      :spo-list="spoList"
      @close="showForm = false"
      @submit="handleSubmit"
    />

    <AppModal
      :show="showDeleteModal"
      title="Подтверждение удаления"
      @close="showDeleteModal = false"
    >
      <p>Вы уверены, что хотите удалить оператора "{{ deletingOperator?.login }}"?</p>

      <template #footer>
        <AppButton variant="secondary" @click="showDeleteModal = false">
          Отмена
        </AppButton>
        <AppButton variant="danger" @click="deleteOperator">
          Удалить
        </AppButton>
      </template>
    </AppModal>

    <AppModal
      :show="showResetModal"
      title="Сброс пароля"
      @close="showResetModal = false"
    >
      <p>Вы уверены, что хотите сбросить пароль оператора "{{ resettingOperator?.login }}"?</p>
      <p class="reset-warning">Текущий пароль станет недействительным.</p>

      <template #footer>
        <AppButton variant="secondary" @click="showResetModal = false">
          Отмена
        </AppButton>
        <AppButton @click="resetPassword">
          Сбросить
        </AppButton>
      </template>
    </AppModal>

    <AppModal
      :show="showPasswordModal"
      :title="isPasswordReset ? 'Пароль сброшен' : 'Оператор создан'"
      @close="showPasswordModal = false"
    >
      <div class="password-info">
        <p v-if="isPasswordReset">Пароль оператора <strong>{{ createdLogin }}</strong> успешно сброшен.</p>
        <p v-else>Оператор <strong>{{ createdLogin }}</strong> успешно создан.</p>
        <p>{{ isPasswordReset ? 'Новый пароль:' : 'Сгенерированный пароль:' }}</p>
        <div class="password-box">
          <code>{{ generatedPassword }}</code>
          <AppButton variant="secondary" @click="copyPassword">
            Копировать
          </AppButton>
        </div>
        <p class="password-warning">
          Сохраните пароль! После закрытия окна его нельзя будет восстановить.
        </p>
      </div>

      <template #footer>
        <AppButton @click="showPasswordModal = false">
          Закрыть
        </AppButton>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.password-info p {
  margin-bottom: 12px;
}

.password-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background-color: #f3f4f6;
  border-radius: 6px;
  margin-bottom: 16px;
}

.password-box code {
  flex: 1;
  font-size: 16px;
  font-family: monospace;
  color: #111827;
}

.password-warning {
  color: #dc2626;
  font-size: 14px;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.reset-warning {
  color: #d97706;
  font-size: 14px;
  margin-top: 8px;
}
</style>
