<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { statsApi } from '../../api/stats'
import AppTable from '../../components/ui/AppTable.vue'

const auth = useAuthStore()
const stats = ref([])
const loading = ref(true)

const columns = [
  { key: 'code', label: 'Код специальности' },
  { key: 'name', label: 'Специальность' },
  { key: 'quota', label: 'Квота', width: '100px' },
  { key: 'enrolled', label: 'Записано', width: '100px' },
  { key: 'available', label: 'Свободно', width: '100px' }
]

const totals = computed(() => {
  const totalQuota = stats.value.reduce((sum, item) => sum + (item.quota || 0), 0)
  const totalEnrolled = stats.value.reduce((sum, item) => sum + item.enrolled, 0)
  return {
    quota: totalQuota,
    enrolled: totalEnrolled,
    available: totalQuota - totalEnrolled
  }
})

onMounted(async () => {
  try {
    stats.value = await statsApi.getStats()
  } catch (error) {
    console.error('Ошибка загрузки статистики:', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="operator-stats">
    <h1 class="page-title">Статистика</h1>
    <p class="spo-name" v-if="auth.user?.spo_name">
      СПО: {{ auth.user.spo_name }}
    </p>

    <div class="totals">
      <div class="total-card">
        <div class="total-value">{{ totals.quota }}</div>
        <div class="total-label">Всего квот</div>
      </div>
      <div class="total-card">
        <div class="total-value">{{ totals.enrolled }}</div>
        <div class="total-label">Записано студентов</div>
      </div>
      <div class="total-card">
        <div class="total-value" :class="{ negative: totals.available < 0 }">
          {{ totals.available }}
        </div>
        <div class="total-label">Свободных мест</div>
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
      <template #available="{ row }">
        <span :class="{ negative: (row.quota || 0) - row.enrolled < 0 }">
          {{ row.quota != null ? (row.quota - row.enrolled) : '-' }}
        </span>
      </template>
    </AppTable>
  </div>
</template>

<style scoped>
.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 8px;
}

.spo-name {
  color: #6b7280;
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

.total-value.negative {
  color: #dc2626;
}

.total-label {
  font-size: 14px;
  color: #6b7280;
}

.negative {
  color: #dc2626;
  font-weight: 600;
}
</style>
