<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { operatorApi } from '../../api/operator'
import { useToastStore } from '../../stores/toast'
import AppButton from '../../components/ui/AppButton.vue'
import AppTable from '../../components/ui/AppTable.vue'
import AppSelect from '../../components/ui/AppSelect.vue'
import StudentForm from '../../components/forms/StudentForm.vue'
import AppModal from '../../components/ui/AppModal.vue'

const toast = useToastStore()

const students = ref([])
const specialties = ref([])
const selectedSpecialty = ref('')
const loading = ref(true)
const showForm = ref(false)
const editingStudent = ref(null)
const showDeleteModal = ref(false)
const deletingStudent = ref(null)
const studentFormRef = ref(null)

const columns = [
  { key: 'id', label: 'ID', width: '80px' },
  { key: 'full_name', label: 'ФИО' },
  { key: 'certificate_number', label: 'Номер аттестата', width: '160px' },
  { key: 'specialty_name', label: 'Направление' },
  { key: 'actions', label: 'Действия', width: '200px' }
]

const specialtyOptions = computed(() => {
  return [
    { value: '', label: 'Все направления' },
    ...specialties.value.map(s => ({
      value: s.id,
      label: `${s.code} - ${s.name}`
    }))
  ]
})

const studentsWithNames = computed(() => {
  return students.value.map(student => {
    const specialty = specialties.value.find(s => s.id === student.specialty_id)
    const fullName = [student.last_name, student.first_name, student.middle_name]
      .filter(Boolean)
      .join(' ')
    return {
      ...student,
      full_name: fullName,
      specialty_name: specialty ? `${specialty.code} - ${specialty.name}` : '-'
    }
  })
})

const filteredStudents = computed(() => {
  if (!selectedSpecialty.value) return studentsWithNames.value
  return studentsWithNames.value.filter(
    s => s.specialty_id === Number(selectedSpecialty.value)
  )
})

onMounted(() => {
  loadData()
})

watch(selectedSpecialty, () => {
  // Фильтрация происходит через computed
})

async function loadData() {
  loading.value = true
  try {
    const [studentData, specialtyData] = await Promise.all([
      operatorApi.getStudents(),
      operatorApi.getSpecialties()
    ])
    students.value = studentData
    specialties.value = specialtyData
  } catch (error) {
    console.error('Ошибка загрузки:', error)
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingStudent.value = null
  showForm.value = true
}

function openEdit(student) {
  editingStudent.value = student
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingStudent.value = null
}

async function handleSubmit(data) {
  try {
    if (editingStudent.value) {
      await operatorApi.updateStudent(editingStudent.value.id, data)
    } else {
      await operatorApi.createStudent(data)
    }
    closeForm()
    await loadData()
  } catch (error) {
    console.error(editingStudent.value ? 'Ошибка обновления:' : 'Ошибка создания:', error)
    if (studentFormRef.value) {
      const message = error.response?.data?.detail || (editingStudent.value ? 'Ошибка при обновлении студента' : 'Ошибка при добавлении студента')
      studentFormRef.value.setError(message)
    }
    throw error
  }
}

function confirmDelete(student) {
  deletingStudent.value = student
  showDeleteModal.value = true
}

async function deleteStudent() {
  if (!deletingStudent.value) return

  try {
    await operatorApi.deleteStudent(deletingStudent.value.id)
    showDeleteModal.value = false
    deletingStudent.value = null
    await loadData()
  } catch (error) {
    console.error('Ошибка удаления:', error)
    toast.error('Ошибка: ' + (error.response?.data?.detail || 'Неизвестная ошибка'))
  }
}
</script>

<template>
  <div class="student-list">
    <div class="page-header">
      <h1 class="page-title">Студенты</h1>
      <AppButton @click="openCreate">Добавить студента</AppButton>
    </div>

    <div class="filters">
      <AppSelect
        v-model="selectedSpecialty"
        :options="specialtyOptions.slice(1)"
        placeholder="Все направления"
        label="Фильтр по направления"
      />
    </div>

    <AppTable
      :columns="columns"
      :data="filteredStudents"
      :loading="loading"
      :page-size="20"
      empty-text="Нет добавленных студентов"
    >
      <template #actions="{ row }">
        <div class="action-buttons">
          <AppButton variant="secondary" @click="openEdit(row)">
            Изменить
          </AppButton>
          <AppButton variant="danger" @click="confirmDelete(row)">
            Удалить
          </AppButton>
        </div>
      </template>
    </AppTable>

    <StudentForm
      ref="studentFormRef"
      :show="showForm"
      :specialties="specialties"
      :selected-specialty-id="selectedSpecialty"
      :student="editingStudent"
      @close="closeForm"
      @submit="handleSubmit"
    />

    <AppModal
      :show="showDeleteModal"
      title="Подтверждение удаления"
      @close="showDeleteModal = false"
    >
      <p>Вы уверены, что хотите удалить студента "{{ deletingStudent?.full_name }}"?</p>

      <template #footer>
        <AppButton variant="secondary" @click="showDeleteModal = false">
          Отмена
        </AppButton>
        <AppButton variant="danger" @click="deleteStudent">
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

.filters {
  margin-bottom: 20px;
  max-width: 300px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}
</style>
