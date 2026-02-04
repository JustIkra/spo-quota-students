<script setup>
import { ref, onMounted, computed } from 'vue'
import { statsApi } from '../../api/stats'
import AppTable from '../../components/ui/AppTable.vue'

const stats = ref([])
const totalStats = ref({ total_quota: 0, total_students: 0 })
const loading = ref(true)

const columns = [
  { key: 'spo_name', label: 'Учреждение' },
  { key: 'code', label: 'Код специальности' },
  { key: 'name', label: 'Специальность' },
  { key: 'quota', label: 'Квота', width: '100px' },
  { key: 'enrolled', label: 'Записано', width: '100px' }
]

const totals = computed(() => {
  return {
    quota: totalStats.value.total_quota,
    enrolled: totalStats.value.total_students
  }
})

onMounted(async () => {
  try {
    const data = await statsApi.getStats()
    totalStats.value = {
      total_quota: data.total_quota || 0,
      total_students: data.total_students || 0
    }
    // Transform nested data to flat array for table
    const flatStats = []
    for (const spo of data.spo_list || []) {
      for (const spec of spo.specialties || []) {
        flatStats.push({
          spo_name: spo.spo_name,
          code: spec.specialty_code || '',
          name: spec.specialty_name,
          quota: spec.quota,
          enrolled: spec.students_count
        })
      }
    }
    stats.value = flatStats
  } catch (error) {
    console.error('Ошибка загрузки статистики:', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="admin-stats">
    <h1 class="page-title">Статистика по всем учреждениям</h1>

    <div class="totals">
      <div class="total-card">
        <div class="total-value">{{ totals.quota }}</div>
        <div class="total-label">Всего квот</div>
      </div>
      <div class="total-card">
        <div class="total-value">{{ totals.enrolled }}</div>
        <div class="total-label">Записано студентов</div>
      </div>
    </div>

    <AppTable
      :columns="columns"
      :data="stats"
      :loading="loading"
      empty-text="Нет данных для отображения"
    >
      <template #quota="{ row }">
        {{ row.quota ?? '-' }}
      </template>
    </AppTable>
  </div>
</template>

<style scoped>
.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 32px;
}

.totals {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.total-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.total-value {
  font-size: 32px;
  font-weight: 700;
  color: #2563eb;
  margin-bottom: 4px;
}

.total-label {
  font-size: 14px;
  color: #6b7280;
}
</style>
