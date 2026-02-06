<script setup>
import { ref, onMounted } from 'vue'
import { operatorApi } from '../../api/operator'
import AppTable from '../../components/ui/AppTable.vue'

const specialties = ref([])
const loading = ref(true)

const columns = [
  { key: 'code', label: 'Код', width: '120px' },
  { key: 'name', label: 'Название' },
  { key: 'quota', label: 'Квота', width: '100px' },
  { key: 'students_count', label: 'Записано', width: '100px' }
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
</script>

<template>
  <div class="specialty-list">
    <div class="page-header">
      <h1 class="page-title">Направления</h1>
    </div>

    <p class="info-text">
      Управление направлениями осуществляется администратором.
      Здесь вы можете просмотреть прикреплённые к вашему учреждению направления.
    </p>

    <AppTable
      :columns="columns"
      :data="specialties"
      :loading="loading"
      :page-size="20"
      empty-text="Нет прикреплённых направлений"
    />
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

.slots-full {
  color: #dc2626;
  font-weight: 600;
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
}

/* Small Mobile: < 480px */
@media (max-width: 479px) {
  .page-title {
    font-size: 20px;
  }
}
</style>
