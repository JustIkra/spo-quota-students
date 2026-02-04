<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '../../api/admin'
import { useToastStore } from '../../stores/toast'
import AppButton from '../../components/ui/AppButton.vue'
import AppTable from '../../components/ui/AppTable.vue'
import SpoForm from '../../components/forms/SpoForm.vue'
import AppModal from '../../components/ui/AppModal.vue'

const toast = useToastStore()

const spoList = ref([])
const loading = ref(true)
const showForm = ref(false)
const editingSpo = ref(null)
const showDeleteModal = ref(false)
const deletingSpo = ref(null)

const columns = [
  { key: 'id', label: 'ID', width: '80px' },
  { key: 'name', label: 'Название' },
  { key: 'created_at', label: 'Дата создания', width: '180px' },
  { key: 'actions', label: 'Действия', width: '200px' }
]

onMounted(() => {
  loadData()
})

async function loadData() {
  loading.value = true
  try {
    spoList.value = await adminApi.getSpoList()
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

function openCreateForm() {
  editingSpo.value = null
  showForm.value = true
}

function openEditForm(spo) {
  editingSpo.value = spo
  showForm.value = true
}

async function handleSubmit(data) {
  try {
    if (editingSpo.value) {
      await adminApi.updateSpo(editingSpo.value.id, data)
    } else {
      await adminApi.createSpo(data)
    }
    showForm.value = false
    await loadData()
  } catch (error) {
    console.error('Ошибка сохранения:', error)
    toast.error('Ошибка сохранения: ' + (error.response?.data?.detail || 'Неизвестная ошибка'))
  }
}

function confirmDelete(spo) {
  deletingSpo.value = spo
  showDeleteModal.value = true
}

async function deleteSpo() {
  if (!deletingSpo.value) return

  try {
    await adminApi.deleteSpo(deletingSpo.value.id)
    showDeleteModal.value = false
    deletingSpo.value = null
    await loadData()
  } catch (error) {
    console.error('Ошибка удаления:', error)
    toast.error('Ошибка удаления: ' + (error.response?.data?.detail || 'Неизвестная ошибка'))
  }
}
</script>

<template>
  <div class="spo-list">
    <div class="page-header">
      <h1 class="page-title">Список СПО</h1>
      <AppButton @click="openCreateForm">Добавить СПО</AppButton>
    </div>

    <AppTable
      :columns="columns"
      :data="spoList"
      :loading="loading"
      empty-text="Нет зарегистрированных СПО"
    >
      <template #created_at="{ value }">
        {{ formatDate(value) }}
      </template>
      <template #actions="{ row }">
        <div class="actions">
          <AppButton variant="secondary" @click="openEditForm(row)">
            Редактировать
          </AppButton>
          <AppButton variant="danger" @click="confirmDelete(row)">
            Удалить
          </AppButton>
        </div>
      </template>
    </AppTable>

    <SpoForm
      :show="showForm"
      :spo="editingSpo"
      @close="showForm = false"
      @submit="handleSubmit"
    />

    <AppModal
      :show="showDeleteModal"
      title="Подтверждение удаления"
      @close="showDeleteModal = false"
    >
      <p>Вы уверены, что хотите удалить СПО "{{ deletingSpo?.name }}"?</p>
      <p class="warning">Это действие также удалит всех связанных операторов, специальности и студентов.</p>

      <template #footer>
        <AppButton variant="secondary" @click="showDeleteModal = false">
          Отмена
        </AppButton>
        <AppButton variant="danger" @click="deleteSpo">
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
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.actions {
  display: flex;
  gap: 8px;
}

.warning {
  color: #dc2626;
  font-size: 14px;
  margin-top: 8px;
}
</style>
