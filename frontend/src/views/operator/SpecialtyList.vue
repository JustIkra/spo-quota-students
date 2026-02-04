<script setup>
import { ref, onMounted } from 'vue'
import { operatorApi } from '../../api/operator'
import AppButton from '../../components/ui/AppButton.vue'
import AppTable from '../../components/ui/AppTable.vue'
import SpecialtyForm from '../../components/forms/SpecialtyForm.vue'
import AppModal from '../../components/ui/AppModal.vue'

const specialties = ref([])
const loading = ref(true)
const showForm = ref(false)
const showDeleteModal = ref(false)
const deletingSpecialty = ref(null)

const columns = [
  { key: 'id', label: 'ID', width: '80px' },
  { key: 'code', label: 'Код', width: '120px' },
  { key: 'name', label: 'Название' },
  { key: 'quota', label: 'Квота', width: '100px' },
  { key: 'actions', label: 'Действия', width: '120px' }
]

onMounted(() => {
  loadData()
})

async function loadData() {
  loading.value = true
  try {
    specialties.value = await operatorApi.getSpecialties()
  } catch (error) {
    console.error('Ошибка загрузки:', error)
  } finally {
    loading.value = false
  }
}

async function handleSubmit(data) {
  try {
    await operatorApi.createSpecialty(data)
    showForm.value = false
    await loadData()
  } catch (error) {
    console.error('Ошибка создания:', error)
    alert('Ошибка: ' + (error.response?.data?.detail || 'Неизвестная ошибка'))
  }
}

function confirmDelete(specialty) {
  deletingSpecialty.value = specialty
  showDeleteModal.value = true
}

async function deleteSpecialty() {
  if (!deletingSpecialty.value) return

  try {
    await operatorApi.deleteSpecialty(deletingSpecialty.value.id)
    showDeleteModal.value = false
    deletingSpecialty.value = null
    await loadData()
  } catch (error) {
    console.error('Ошибка удаления:', error)
    alert('Ошибка: ' + (error.response?.data?.detail || 'Неизвестная ошибка'))
  }
}
</script>

<template>
  <div class="specialty-list">
    <div class="page-header">
      <h1 class="page-title">Специальности</h1>
      <AppButton @click="showForm = true">Добавить специальность</AppButton>
    </div>

    <AppTable
      :columns="columns"
      :data="specialties"
      :loading="loading"
      empty-text="Нет добавленных специальностей"
    >
      <template #quota="{ row }">
        {{ row.quota ?? 'По умолч.' }}
      </template>
      <template #actions="{ row }">
        <AppButton variant="danger" @click="confirmDelete(row)">
          Удалить
        </AppButton>
      </template>
    </AppTable>

    <SpecialtyForm
      :show="showForm"
      @close="showForm = false"
      @submit="handleSubmit"
    />

    <AppModal
      :show="showDeleteModal"
      title="Подтверждение удаления"
      @close="showDeleteModal = false"
    >
      <p>Вы уверены, что хотите удалить специальность "{{ deletingSpecialty?.name }}"?</p>
      <p class="warning">Все студенты этой специальности также будут удалены.</p>

      <template #footer>
        <AppButton variant="secondary" @click="showDeleteModal = false">
          Отмена
        </AppButton>
        <AppButton variant="danger" @click="deleteSpecialty">
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

.warning {
  color: #dc2626;
  font-size: 14px;
  margin-top: 8px;
}
</style>
