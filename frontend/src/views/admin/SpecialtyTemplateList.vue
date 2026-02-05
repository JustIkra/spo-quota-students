<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '../../api/admin'
import { useToastStore } from '../../stores/toast'
import AppButton from '../../components/ui/AppButton.vue'
import AppTable from '../../components/ui/AppTable.vue'
import AppModal from '../../components/ui/AppModal.vue'
import AppInput from '../../components/ui/AppInput.vue'

const toast = useToastStore()

const templates = ref([])
const loading = ref(true)
const showForm = ref(false)
const showDeleteModal = ref(false)
const editingTemplate = ref(null)
const deletingTemplate = ref(null)

const form = ref({ code: '', name: '' })
const errors = ref({})
const formLoading = ref(false)

const columns = [
  { key: 'code', label: 'Код', width: '150px' },
  { key: 'name', label: 'Название' },
  { key: 'spo_count', label: 'Учреждений', width: '120px' },
  { key: 'actions', label: 'Действия', width: '180px' }
]

onMounted(() => {
  loadData()
})

async function loadData() {
  loading.value = true
  try {
    templates.value = await adminApi.getSpecialtyTemplates()
  } catch (error) {
    console.error('Ошибка загрузки:', error)
    toast.error('Ошибка загрузки справочника')
  } finally {
    loading.value = false
  }
}

function openCreateForm() {
  editingTemplate.value = null
  form.value = { code: '', name: '' }
  errors.value = {}
  showForm.value = true
}

function openEditForm(template) {
  editingTemplate.value = template
  form.value = { code: template.code, name: template.name }
  errors.value = {}
  showForm.value = true
}

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

async function handleSubmit() {
  if (!validate()) return

  formLoading.value = true
  try {
    if (editingTemplate.value) {
      await adminApi.updateSpecialtyTemplate(editingTemplate.value.id, form.value)
      toast.success('Направление обновлена')
    } else {
      await adminApi.createSpecialtyTemplate(form.value)
      toast.success('Направление добавлена в справочник')
    }
    showForm.value = false
    await loadData()
  } catch (error) {
    console.error('Ошибка:', error)
    toast.error(error.response?.data?.detail || 'Произошла ошибка')
  } finally {
    formLoading.value = false
  }
}

function confirmDelete(template) {
  deletingTemplate.value = template
  showDeleteModal.value = true
}

async function deleteTemplate() {
  if (!deletingTemplate.value) return

  try {
    await adminApi.deleteSpecialtyTemplate(deletingTemplate.value.id)
    toast.success('Направление удалена из справочника')
    showDeleteModal.value = false
    deletingTemplate.value = null
    await loadData()
  } catch (error) {
    console.error('Ошибка удаления:', error)
    toast.error(error.response?.data?.detail || 'Ошибка удаления')
  }
}
</script>

<template>
  <div class="specialty-template-list">
    <div class="page-header">
      <h1 class="page-title">Справочник направлений</h1>
      <AppButton @click="openCreateForm">Добавить в справочник</AppButton>
    </div>

    <p class="info-text">
      Глобальный справочник направлений.
      Отсюда администратор прикрепляет направления к учреждениям.
    </p>

    <AppTable
      :columns="columns"
      :data="templates"
      :loading="loading"
      empty-text="Справочник пуст"
    >
      <template #spo_count="{ row }">
        <span class="usage-badge" :class="{ 'in-use': row.spo_count > 0 }">
          {{ row.spo_count }}
        </span>
      </template>
      <template #actions="{ row }">
        <div class="actions">
          <AppButton variant="secondary" @click="openEditForm(row)">
            Изменить
          </AppButton>
          <AppButton variant="danger" @click="confirmDelete(row)">
            Удалить
          </AppButton>
        </div>
      </template>
    </AppTable>

    <!-- Form Modal -->
    <AppModal
      :show="showForm"
      :title="editingTemplate ? 'Редактировать направление' : 'Новая направление'"
      @close="showForm = false"
    >
      <form class="form" @submit.prevent="handleSubmit">
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
        <AppButton variant="secondary" @click="showForm = false">
          Отмена
        </AppButton>
        <AppButton :loading="formLoading" @click="handleSubmit">
          {{ editingTemplate ? 'Сохранить' : 'Добавить' }}
        </AppButton>
      </template>
    </AppModal>

    <!-- Delete Confirmation Modal -->
    <AppModal
      :show="showDeleteModal"
      title="Подтверждение удаления"
      @close="showDeleteModal = false"
    >
      <p>Вы уверены, что хотите удалить направление "{{ deletingTemplate?.name }}" из справочника?</p>
      <p v-if="deletingTemplate?.spo_count > 0" class="warning">
        Эта направление прикреплена к {{ deletingTemplate?.spo_count }} учреждениям.
        При удалении будут удалены все привязки и записанные студенты.
      </p>

      <template #footer>
        <AppButton variant="secondary" @click="showDeleteModal = false">
          Отмена
        </AppButton>
        <AppButton variant="danger" @click="deleteTemplate">
          Удалить
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
  margin-bottom: 16px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.info-text {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 24px;
  padding: 12px 16px;
  background: #f3f4f6;
  border-radius: 8px;
}

.actions {
  display: flex;
  gap: 8px;
}

.usage-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: #f3f4f6;
  color: #6b7280;
}

.usage-badge.in-use {
  background: #dbeafe;
  color: #2563eb;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.warning {
  color: #dc2626;
  font-size: 14px;
  margin-top: 8px;
}
</style>
