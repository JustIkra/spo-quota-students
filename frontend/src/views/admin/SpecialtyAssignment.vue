<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { adminApi } from '../../api/admin'
import { useToastStore } from '../../stores/toast'
import AppButton from '../../components/ui/AppButton.vue'
import AppTable from '../../components/ui/AppTable.vue'
import AppModal from '../../components/ui/AppModal.vue'
import AppSelect from '../../components/ui/AppSelect.vue'
import AppInput from '../../components/ui/AppInput.vue'

const toast = useToastStore()

const specialties = ref([])
const spoList = ref([])
const templates = ref([])
const loading = ref(true)
const selectedSpoId = ref('')

const showAssignModal = ref(false)
const showDeleteModal = ref(false)
const showQuotaModal = ref(false)
const showSettingsModal = ref(false)
const deletingSpecialty = ref(null)
const editingSpecialty = ref(null)

const assignForm = ref({ template_id: '', spo_id: '', quota: '' })
const assignErrors = ref({})
const assignLoading = ref(false)

const quotaForm = ref({ quota: '' })
const quotaLoading = ref(false)

const settings = ref({ base_quota: 30 })
const settingsLoading = ref(false)

const columns = [
  { key: 'code', label: 'Код', width: '120px' },
  { key: 'name', label: 'Название' },
  { key: 'spo_name', label: 'Учреждение' },
  { key: 'quota', label: 'Квота', width: '100px' },
  { key: 'students_count', label: 'Записано', width: '100px' },
  { key: 'actions', label: 'Действия', width: '180px' }
]

const spoOptions = computed(() => [
  { value: '', label: 'Все учреждения' },
  ...spoList.value.map(spo => ({
    value: spo.id,
    label: spo.name
  }))
])

const templateOptions = computed(() => templates.value.map(t => ({
  value: t.id,
  label: `${t.code} - ${t.name}`
})))

const assignSpoOptions = computed(() => spoList.value.map(spo => ({
  value: spo.id,
  label: spo.name
})))

onMounted(async () => {
  await Promise.all([loadSpoList(), loadTemplates(), loadSettings()])
  await loadSpecialties()
})

async function loadSettings() {
  try {
    settings.value = await adminApi.getSettings()
  } catch (error) {
    console.error('Ошибка загрузки настроек:', error)
  }
}

async function saveSettings() {
  settingsLoading.value = true
  try {
    await adminApi.updateSettings({ base_quota: Number(settings.value.base_quota) })
    toast.success('Базовая квота сохранена')
    showSettingsModal.value = false
  } catch (error) {
    console.error('Ошибка сохранения:', error)
    toast.error('Ошибка сохранения настроек')
  } finally {
    settingsLoading.value = false
  }
}

watch(selectedSpoId, () => {
  loadSpecialties()
})

async function loadSpoList() {
  try {
    spoList.value = await adminApi.getSpoList()
  } catch (error) {
    console.error('Ошибка загрузки учреждений:', error)
  }
}

async function loadTemplates() {
  try {
    templates.value = await adminApi.getSpecialtyTemplates()
  } catch (error) {
    console.error('Ошибка загрузки справочника:', error)
  }
}

async function loadSpecialties() {
  loading.value = true
  try {
    const spoId = selectedSpoId.value || null
    specialties.value = await adminApi.getSpecialties(spoId)
  } catch (error) {
    console.error('Ошибка загрузки:', error)
    toast.error('Ошибка загрузки направлений')
  } finally {
    loading.value = false
  }
}

function openAssignModal() {
  assignForm.value = { template_id: '', spo_id: selectedSpoId.value || '', quota: '' }
  assignErrors.value = {}
  showAssignModal.value = true
}

function validateAssign() {
  assignErrors.value = {}
  if (!assignForm.value.template_id) {
    assignErrors.value.template_id = 'Выберите направление'
  }
  if (!assignForm.value.spo_id) {
    assignErrors.value.spo_id = 'Выберите учреждение'
  }
  if (assignForm.value.quota && (isNaN(assignForm.value.quota) || Number(assignForm.value.quota) < 0)) {
    assignErrors.value.quota = 'Квота должна быть положительным числом'
  }
  return Object.keys(assignErrors.value).length === 0
}

async function handleAssign() {
  if (!validateAssign()) return

  assignLoading.value = true
  try {
    const data = {
      template_id: Number(assignForm.value.template_id),
      spo_id: Number(assignForm.value.spo_id)
    }
    if (assignForm.value.quota) {
      data.quota = Number(assignForm.value.quota)
    }
    await adminApi.assignSpecialtyToSpo(data)
    toast.success('Направление прикреплена к учреждению')
    showAssignModal.value = false
    await loadSpecialties()
  } catch (error) {
    console.error('Ошибка:', error)
    toast.error(error.response?.data?.detail || 'Произошла ошибка')
  } finally {
    assignLoading.value = false
  }
}

function openQuotaModal(specialty) {
  editingSpecialty.value = specialty
  quotaForm.value = { quota: specialty.quota }
  showQuotaModal.value = true
}

async function handleQuotaUpdate() {
  if (!editingSpecialty.value) return

  quotaLoading.value = true
  try {
    await adminApi.updateSpecialtyQuota(editingSpecialty.value.id, Number(quotaForm.value.quota))
    toast.success('Квота обновлена')
    showQuotaModal.value = false
    await loadSpecialties()
  } catch (error) {
    console.error('Ошибка:', error)
    toast.error(error.response?.data?.detail || 'Ошибка обновления квоты')
  } finally {
    quotaLoading.value = false
  }
}

function confirmDelete(specialty) {
  deletingSpecialty.value = specialty
  showDeleteModal.value = true
}

async function deleteSpecialty() {
  if (!deletingSpecialty.value) return

  try {
    await adminApi.deleteSpecialty(deletingSpecialty.value.id)
    toast.success('Направление откреплена от учреждения')
    showDeleteModal.value = false
    deletingSpecialty.value = null
    await loadSpecialties()
  } catch (error) {
    console.error('Ошибка удаления:', error)
    toast.error(error.response?.data?.detail || 'Ошибка удаления')
  }
}
</script>

<template>
  <div class="specialty-assignment">
    <div class="page-header">
      <h1 class="page-title">Направления учреждений</h1>
      <div class="header-actions">
        <AppButton variant="secondary" @click="showSettingsModal = true">
          Базовая квота: {{ settings.base_quota }}
        </AppButton>
        <AppButton @click="openAssignModal">Прикрепить направление</AppButton>
      </div>
    </div>

    <div class="filters">
      <AppSelect
        v-model="selectedSpoId"
        label="Фильтр по учреждению"
        :options="spoOptions"
      />
    </div>

    <AppTable
      :columns="columns"
      :data="specialties"
      :loading="loading"
      empty-text="Нет прикреплённых направлений"
    >
      <template #actions="{ row }">
        <div class="actions">
          <AppButton variant="secondary" @click="openQuotaModal(row)">
            Квота
          </AppButton>
          <AppButton variant="danger" @click="confirmDelete(row)">
            Открепить
          </AppButton>
        </div>
      </template>
    </AppTable>

    <!-- Assign Modal -->
    <AppModal
      :show="showAssignModal"
      title="Прикрепить направление"
      @close="showAssignModal = false"
    >
      <form class="form" @submit.prevent="handleAssign">
        <AppSelect
          v-model="assignForm.template_id"
          label="Направление (из справочника)"
          :options="templateOptions"
          :error="assignErrors.template_id"
          required
        />
        <AppSelect
          v-model="assignForm.spo_id"
          label="Учреждение"
          :options="assignSpoOptions"
          :error="assignErrors.spo_id"
          required
        />
        <AppInput
          v-model="assignForm.quota"
          label="Квота (необязательно)"
          placeholder="Если не указать, будет взята из настроек"
          type="number"
          :error="assignErrors.quota"
        />
      </form>

      <template #footer>
        <AppButton variant="secondary" @click="showAssignModal = false">
          Отмена
        </AppButton>
        <AppButton :loading="assignLoading" @click="handleAssign">
          Прикрепить
        </AppButton>
      </template>
    </AppModal>

    <!-- Quota Modal -->
    <AppModal
      :show="showQuotaModal"
      title="Изменить квоту"
      @close="showQuotaModal = false"
    >
      <p class="modal-info">
        {{ editingSpecialty?.code }} - {{ editingSpecialty?.name }}<br>
        <small>{{ editingSpecialty?.spo_name }}</small>
      </p>
      <form class="form" @submit.prevent="handleQuotaUpdate">
        <AppInput
          v-model="quotaForm.quota"
          label="Квота"
          type="number"
          min="0"
          required
        />
      </form>

      <template #footer>
        <AppButton variant="secondary" @click="showQuotaModal = false">
          Отмена
        </AppButton>
        <AppButton :loading="quotaLoading" @click="handleQuotaUpdate">
          Сохранить
        </AppButton>
      </template>
    </AppModal>

    <!-- Delete Confirmation Modal -->
    <AppModal
      :show="showDeleteModal"
      title="Подтверждение открепления"
      @close="showDeleteModal = false"
    >
      <p>
        Вы уверены, что хотите открепить направление
        "{{ deletingSpecialty?.name }}" от учреждения "{{ deletingSpecialty?.spo_name }}"?
      </p>
      <p v-if="deletingSpecialty?.students_count > 0" class="warning">
        Записано студентов: {{ deletingSpecialty?.students_count }}.
        При откреплении все студенты будут удалены.
      </p>

      <template #footer>
        <AppButton variant="secondary" @click="showDeleteModal = false">
          Отмена
        </AppButton>
        <AppButton variant="danger" @click="deleteSpecialty">
          Открепить
        </AppButton>
      </template>
    </AppModal>

    <!-- Settings Modal -->
    <AppModal
      :show="showSettingsModal"
      title="Базовая квота по умолчанию"
      @close="showSettingsModal = false"
    >
      <p class="settings-hint">
        Это значение используется для новых направлений, если квота не указана явно.
      </p>
      <form class="form" @submit.prevent="saveSettings">
        <AppInput
          v-model="settings.base_quota"
          label="Квота по умолчанию"
          type="number"
          min="0"
          required
        />
      </form>

      <template #footer>
        <AppButton variant="secondary" @click="showSettingsModal = false">
          Отмена
        </AppButton>
        <AppButton :loading="settingsLoading" @click="saveSettings">
          Сохранить
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

.header-actions {
  display: flex;
  gap: 12px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.filters {
  margin-bottom: 24px;
  max-width: 300px;
}

.actions {
  display: flex;
  gap: 8px;
}

.slots-full {
  color: #dc2626;
  font-weight: 600;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-info {
  margin-bottom: 16px;
  padding: 12px;
  background: #f3f4f6;
  border-radius: 8px;
}

.modal-info small {
  color: #6b7280;
}

.warning {
  color: #dc2626;
  font-size: 14px;
  margin-top: 8px;
}

.settings-hint {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 16px;
}
</style>
