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
const createdSpoName = ref('')
const isPasswordReset = ref(false)

const showBulkConfirmModal = ref(false)
const showBulkResultModal = ref(false)
const bulkCreated = ref([])
const bulkLoading = ref(false)
const exportingDocx = ref(false)

const spoWithoutOperatorCount = computed(() => {
  const occupied = new Set(operators.value.map(op => op.spo_id))
  return spoList.value.filter(s => !occupied.has(s.id)).length
})

const columns = [
  { key: 'id', label: 'ID', width: '80px' },
  { key: 'login', label: 'Логин' },
  { key: 'spo_name', label: 'Учреждение' },
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

    createdLogin.value = result.login
    generatedPassword.value = result.generated_password
    createdSpoName.value = spoList.value.find(s => s.id === result.spo_id)?.name || ''
    isPasswordReset.value = false
    showPasswordModal.value = true

    await loadData()
  } catch (error) {
    console.error('Ошибка создания:', error)
    toast.error('Ошибка создания: ' + (error.response?.data?.detail || 'Неизвестная ошибка'))
  }
}

function openBulkConfirm() {
  if (spoWithoutOperatorCount.value === 0) {
    toast.info('У всех учреждений уже есть операторы')
    return
  }
  showBulkConfirmModal.value = true
}

async function runBulkCreate() {
  bulkLoading.value = true
  try {
    const result = await adminApi.createOperatorsBulk()
    bulkCreated.value = result.created || []
    showBulkConfirmModal.value = false
    if (bulkCreated.value.length === 0) {
      toast.info('Новых операторов создавать не для кого')
    } else {
      showBulkResultModal.value = true
      toast.success(`Создано операторов: ${bulkCreated.value.length}`)
    }
    await loadData()
  } catch (error) {
    console.error('Ошибка массового создания:', error)
    toast.error('Ошибка создания: ' + (error.response?.data?.detail || 'Неизвестная ошибка'))
  } finally {
    bulkLoading.value = false
  }
}

function extractFilename(disposition, fallback) {
  if (!disposition) return fallback
  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match) {
    try { return decodeURIComponent(utf8Match[1]) } catch { /* ignore */ }
  }
  const plainMatch = disposition.match(/filename="?([^";]+)"?/i)
  return plainMatch ? plainMatch[1] : fallback
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function downloadDocx(items, fallbackName) {
  if (!items.length) return
  exportingDocx.value = true
  try {
    const response = await adminApi.exportOperatorsDocx(items)
    const filename = extractFilename(response.headers?.['content-disposition'], fallbackName)
    triggerDownload(response.data, filename)
  } catch (error) {
    console.error('Ошибка скачивания .docx:', error)
    toast.error('Не удалось сформировать .docx')
  } finally {
    exportingDocx.value = false
  }
}

function downloadBulkDocx() {
  downloadDocx(bulkCreated.value, 'operatory.docx')
}

function downloadSingleDocx() {
  downloadDocx(
    [{
      spo_name: createdSpoName.value || '-',
      login: createdLogin.value,
      password: generatedPassword.value,
    }],
    `operator_${createdLogin.value}.docx`
  )
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

    createdLogin.value = result.login
    generatedPassword.value = result.generated_password
    createdSpoName.value = spoList.value.find(s => s.id === result.spo_id)?.name || ''
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
      <div class="page-actions">
        <AppButton
          variant="secondary"
          :disabled="bulkLoading || spoWithoutOperatorCount === 0"
          @click="openBulkConfirm"
        >
          Создать для всех ({{ spoWithoutOperatorCount }})
        </AppButton>
        <AppButton @click="showForm = true">Добавить оператора</AppButton>
      </div>
    </div>

    <AppTable
      :columns="columns"
      :data="operatorsWithSpo"
      :loading="loading"
      :page-size="20"
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
        <p v-if="createdSpoName" class="spo-name-line">Учреждение: <strong>{{ createdSpoName }}</strong></p>
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
        <AppButton variant="secondary" :disabled="exportingDocx" @click="downloadSingleDocx">
          Скачать .docx
        </AppButton>
        <AppButton @click="showPasswordModal = false">
          Закрыть
        </AppButton>
      </template>
    </AppModal>

    <AppModal
      :show="showBulkConfirmModal"
      title="Создать операторов для всех учреждений"
      @close="showBulkConfirmModal = false"
    >
      <p>
        Будут созданы операторы для
        <strong>{{ spoWithoutOperatorCount }}</strong>
        учреждений, у которых их ещё нет.
      </p>
      <p class="reset-warning">
        После завершения вы сможете скачать .docx со всеми логинами и паролями.
        Сохраните файл сразу — пароли в открытом виде больше нигде не отображаются.
      </p>

      <template #footer>
        <AppButton variant="secondary" :disabled="bulkLoading" @click="showBulkConfirmModal = false">
          Отмена
        </AppButton>
        <AppButton :disabled="bulkLoading" @click="runBulkCreate">
          {{ bulkLoading ? 'Создание…' : 'Создать' }}
        </AppButton>
      </template>
    </AppModal>

    <AppModal
      :show="showBulkResultModal"
      title="Операторы созданы"
      width="900px"
      @close="showBulkResultModal = false"
    >
      <p>
        Создано операторов: <strong>{{ bulkCreated.length }}</strong>.
        Скачайте .docx — после закрытия окна пароли восстановить нельзя.
      </p>

      <div class="bulk-table-wrap">
        <table class="bulk-table">
          <thead>
            <tr>
              <th>Учреждение</th>
              <th>Логин</th>
              <th>Пароль</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in bulkCreated" :key="item.spo_id">
              <td>{{ item.spo_name }}</td>
              <td><code>{{ item.login }}</code></td>
              <td><code>{{ item.password }}</code></td>
            </tr>
          </tbody>
        </table>
      </div>

      <template #footer>
        <AppButton variant="secondary" :disabled="exportingDocx" @click="downloadBulkDocx">
          {{ exportingDocx ? 'Формирование…' : 'Скачать .docx' }}
        </AppButton>
        <AppButton @click="showBulkResultModal = false">
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

.page-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.password-info p {
  margin-bottom: 12px;
}

.spo-name-line {
  color: #374151;
}

.bulk-table-wrap {
  margin-top: 12px;
  max-height: 50vh;
  overflow: auto;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.bulk-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.bulk-table th,
.bulk-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
  vertical-align: top;
  word-break: break-word;
}

.bulk-table th {
  background-color: #f9fafb;
  font-weight: 600;
  color: #111827;
  position: sticky;
  top: 0;
}

.bulk-table tbody tr:last-child td {
  border-bottom: none;
}

.bulk-table code {
  font-family: monospace;
  color: #111827;
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

/* Mobile: 480px - 767px */
@media (max-width: 767px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .page-title {
    font-size: 22px;
    word-break: break-word;
  }

  .page-actions {
    flex-direction: column;
  }

  .page-actions > * {
    width: 100%;
  }

  .action-buttons {
    display: flex;
    gap: 8px;
    width: 100%;
  }

  .action-buttons > * {
    flex: 1;
  }

  .password-box {
    flex-direction: column;
    align-items: stretch;
  }

  .bulk-table {
    font-size: 13px;
  }

  .bulk-table th,
  .bulk-table td {
    padding: 6px 8px;
  }
}

/* Small Mobile: < 480px */
@media (max-width: 479px) {
  .page-title {
    font-size: 20px;
  }
}
</style>
