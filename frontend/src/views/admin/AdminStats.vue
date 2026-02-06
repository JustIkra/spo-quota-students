<script setup>
import { ref, onMounted, computed } from 'vue'
import { statsApi } from '../../api/stats'
import AppSelect from '../../components/ui/AppSelect.vue'

const stats = ref(null)
const loading = ref(true)
const searchQuery = ref('')
const sortBy = ref('name') // 'name', 'fill', 'students'

const sortOptions = [
  { value: 'name', label: 'По названию' },
  { value: 'fill', label: 'По заполненности' },
  { value: 'students', label: 'По числу студентов' }
]

const totals = computed(() => {
  if (!spoCards.value.length) return { quota: 0, enrolled: 0, available: 0, overQuota: 0, spo: 0, specialties: 0 }
  let quota = 0
  let enrolled = 0
  let specialtiesCount = 0
  for (const spo of spoCards.value) {
    quota += spo.total_quota || 0
    enrolled += spo.total_students || 0
    specialtiesCount += spo.specialties?.length || 0
  }
  return {
    quota,
    enrolled,
    available: Math.max(0, quota - enrolled),
    overQuota: Math.max(0, enrolled - quota),
    spo: spoCards.value.length,
    specialties: specialtiesCount
  }
})

const fillPercent = computed(() => {
  if (!totals.value.quota) return 0
  return Math.round((totals.value.enrolled / totals.value.quota) * 100)
})

const spoCards = computed(() => {
  if (!stats.value || !stats.value.spo_list) return []

  let list = [...stats.value.spo_list]

  // Filter by search
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    list = list.filter(spo => spo.spo_name.toLowerCase().includes(query))
  }

  // Sort
  if (sortBy.value === 'fill') {
    list.sort((a, b) => {
      const fillA = a.total_quota ? (a.total_students / a.total_quota) : 0
      const fillB = b.total_quota ? (b.total_students / b.total_quota) : 0
      return fillB - fillA
    })
  } else if (sortBy.value === 'students') {
    list.sort((a, b) => b.total_students - a.total_students)
  } else {
    list.sort((a, b) => a.spo_name.localeCompare(b.spo_name, 'ru'))
  }

  return list
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

function getProgressPercent(enrolled, quota) {
  if (!quota) return 0
  return Math.min(100, Math.round((enrolled / quota) * 100))
}

function getProgressColor(percent) {
  if (percent >= 100) return '#dc2626'
  if (percent >= 75) return '#f59e0b'
  return '#10b981'
}

function getAvailableSlots(spo) {
  return Math.max(0, spo.total_quota - spo.total_students)
}
</script>

<template>
  <div class="admin-stats">
    <h1 class="page-title">Статистика набора</h1>

    <div v-if="loading" class="loading">
      Загрузка...
    </div>

    <template v-else>
      <!-- Overall Summary -->
      <div class="summary-section">
        <div class="summary-header">
          <h2 class="summary-title">Общий набор по всем учреждениям</h2>
        </div>

        <div class="summary-progress">
          <div class="progress-bar large">
            <div
              v-if="fillPercent > 0"
              class="progress-fill"
              :style="{
                width: Math.min(100, fillPercent) + '%',
                backgroundColor: getProgressColor(fillPercent)
              }"
            ></div>
          </div>
        </div>

        <div class="summary-stats">
          <div class="summary-stat">
            <span class="stat-value enrolled">{{ totals.enrolled }}</span>
            <span class="stat-label">записано студентов</span>
          </div>
          <div class="summary-divider">из</div>
          <div class="summary-stat">
            <span class="stat-value quota">{{ totals.quota }}</span>
            <span class="stat-label">мест по квотам</span>
          </div>
        </div>
      </div>

      <!-- Quick Stats Cards -->
      <div class="quick-stats">
        <div class="quick-stat-card">
          <div class="quick-stat-value">{{ totals.spo }}</div>
          <div class="quick-stat-label">учреждений</div>
        </div>
        <div class="quick-stat-card">
          <div class="quick-stat-value">{{ totals.specialties }}</div>
          <div class="quick-stat-label">направлений</div>
        </div>
        <div class="quick-stat-card available">
          <div class="quick-stat-value">{{ totals.available }}</div>
          <div class="quick-stat-label">осталось мест</div>
        </div>
        <div class="quick-stat-card over-quota" v-if="totals.overQuota > 0">
          <div class="quick-stat-value">{{ totals.overQuota }}</div>
          <div class="quick-stat-label">сверх квоты</div>
        </div>
      </div>

      <!-- Filters and Sort -->
      <div class="controls">
        <div class="search-box">
          <label class="search-label">Поиск</label>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Поиск по названию учреждения..."
            class="search-input"
          />
        </div>
        <div class="sort-box">
          <AppSelect
            v-model="sortBy"
            :options="sortOptions"
            label="Сортировка"
          />
        </div>
      </div>

      <!-- SPO List Header -->
      <div class="spo-list-header">
        <h2 class="section-title">Статистика по учреждениям</h2>
        <span class="spo-count">{{ spoCards.length }} из {{ stats?.total_spo || 0 }}</span>
      </div>

      <!-- SPO Cards -->
      <div v-if="spoCards.length === 0" class="empty">
        <template v-if="searchQuery">
          Учреждения не найдены по запросу "{{ searchQuery }}"
        </template>
        <template v-else>
          Нет данных для отображения
        </template>
      </div>

      <div v-else class="spo-cards">
        <div v-for="spo in spoCards" :key="spo.spo_id" class="spo-card">
          <div class="spo-header">
            <h3 class="spo-name">{{ spo.spo_name }}</h3>
            <div class="spo-summary">
              <span class="spo-summary-label">Записано / Квота:</span>
              <span class="spo-students">{{ spo.total_students }}</span>
              <span class="spo-separator">/</span>
              <span class="spo-quota">{{ spo.total_quota }}</span>
              <span class="spo-available" v-if="getAvailableSlots(spo) > 0">
                (ещё {{ getAvailableSlots(spo) }})
              </span>
              <span class="spo-full" v-else-if="spo.total_quota > 0">
                (заполнено)
              </span>
            </div>
          </div>

          <div class="spo-progress">
            <div class="progress-bar">
              <div
                v-if="getProgressPercent(spo.total_students, spo.total_quota) > 0"
                class="progress-fill"
                :style="{
                  width: getProgressPercent(spo.total_students, spo.total_quota) + '%',
                  backgroundColor: getProgressColor(getProgressPercent(spo.total_students, spo.total_quota))
                }"
              ></div>
            </div>
            <span class="progress-text">
              {{ getProgressPercent(spo.total_students, spo.total_quota) }}%
            </span>
          </div>

          <div v-if="spo.specialties && spo.specialties.length > 0" class="specialties-list">
            <div class="specialties-header">
              <span class="col-name">Направление</span>
              <span class="col-stats">Записано / Квота</span>
            </div>
            <div
              v-for="spec in spo.specialties"
              :key="spec.specialty_id"
              class="specialty-row"
            >
              <div class="specialty-info">
                <span class="specialty-code" v-if="spec.specialty_code">{{ spec.specialty_code }}</span>
                <span class="specialty-name">{{ spec.specialty_name }}</span>
              </div>
              <div class="specialty-stats">
                <span class="stat-enrolled">{{ spec.students_count }}</span>
                <span class="stat-separator">/</span>
                <span class="stat-quota">{{ spec.quota }}</span>
                <span
                  class="stat-available"
                  :class="{ full: spec.students_count >= spec.quota }"
                >
                  {{ spec.students_count >= spec.quota ? 'заполнено' : `ещё ${spec.quota - spec.students_count}` }}
                </span>
                <div class="mini-progress">
                  <div
                    v-if="getProgressPercent(spec.students_count, spec.quota) > 0"
                    class="mini-progress-fill"
                    :style="{
                      width: getProgressPercent(spec.students_count, spec.quota) + '%',
                      backgroundColor: getProgressColor(getProgressPercent(spec.students_count, spec.quota))
                    }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="no-specialties">
            Нет прикреплённых направлений
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 24px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

/* Summary Section */
.summary-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 24px;
  margin-bottom: 24px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.summary-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.summary-fill {
  font-size: 24px;
  font-weight: 700;
}

.summary-progress {
  margin-bottom: 20px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar.large {
  height: 12px;
  border-radius: 6px;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  transition: width 0.3s ease;
}

.summary-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.summary-stat {
  text-align: center;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  display: block;
}

.stat-value.enrolled {
  color: #2563eb;
}

.stat-value.quota {
  color: #6b7280;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

.summary-divider {
  font-size: 18px;
  color: #9ca3af;
}

/* Quick Stats */
.quick-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.quick-stat-card {
  background: white;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.quick-stat-card.available {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.quick-stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 4px;
}

.quick-stat-card.available .quick-stat-value {
  color: #16a34a;
}

.quick-stat-card.over-quota {
  background: #fff7ed;
  border: 1px solid #fed7aa;
}

.quick-stat-card.over-quota .quick-stat-value {
  color: #ea580c;
}

.quick-stat-card.over-quota .quick-stat-label {
  color: #c2410c;
  font-weight: 500;
}

.quick-stat-label {
  font-size: 13px;
  color: #6b7280;
}

/* Controls */
.controls {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  align-items: flex-end;
}

.search-box {
  flex: 1;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.search-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.search-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
  outline: none;
  transition: all 0.2s ease;
}

.search-input:hover {
  border-color: #9ca3af;
  background-color: #fafafa;
}

.search-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
  background-color: white;
}

.sort-box {
  min-width: 180px;
}

/* SPO List Header */
.spo-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.spo-count {
  font-size: 14px;
  color: #6b7280;
}

.empty {
  text-align: center;
  padding: 40px;
  color: #6b7280;
  background: #f9fafb;
  border-radius: 12px;
}

/* SPO Cards */
.spo-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.spo-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.spo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.spo-name {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin: 0;
  flex: 1;
  max-width: 60%;
}

.spo-summary {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  flex-shrink: 0;
}

.spo-summary-label {
  color: #6b7280;
  margin-right: 4px;
}

.spo-students {
  font-weight: 600;
  color: #2563eb;
}

.spo-separator {
  color: #9ca3af;
}

.spo-quota {
  color: #6b7280;
}

.spo-available {
  color: #16a34a;
  font-size: 13px;
  margin-left: 4px;
}

.spo-full {
  color: #dc2626;
  font-size: 13px;
  margin-left: 4px;
}

.spo-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: #fafafa;
  border-bottom: 1px solid #e5e7eb;
}

.progress-text {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  min-width: 40px;
  text-align: right;
}

/* Specialties List */
.specialties-list {
  padding: 8px 20px 12px;
}

.specialties-header {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 12px;
  font-weight: 500;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #e5e7eb;
}

.specialty-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
}

.specialty-row:last-child {
  border-bottom: none;
}

.specialty-info {
  display: flex;
  gap: 12px;
  align-items: center;
}

.specialty-code {
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  min-width: 70px;
}

.specialty-name {
  font-size: 14px;
  color: #111827;
}

.specialty-stats {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-enrolled {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.stat-separator {
  color: #9ca3af;
}

.stat-quota {
  font-size: 14px;
  color: #6b7280;
}

.stat-available {
  font-size: 12px;
  color: #16a34a;
  margin-left: 8px;
  min-width: 70px;
  text-align: right;
}

.stat-available.full {
  color: #dc2626;
}

.mini-progress {
  width: 50px;
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
  margin-left: 8px;
}

.mini-progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.no-specialties {
  padding: 20px;
  text-align: center;
  color: #9ca3af;
  font-size: 14px;
}

/* Tablet: 768px - 1023px */
@media (max-width: 1023px) {
  .stat-value {
    font-size: 28px;
  }
}

/* Mobile: 480px - 767px */
@media (max-width: 767px) {
  .page-title {
    font-size: 22px;
    word-break: break-word;
  }

  .summary-stats {
    flex-direction: column;
    gap: 8px;
  }

  .summary-divider {
    font-size: 14px;
  }

  .stat-value {
    font-size: 28px;
  }

  .controls {
    flex-direction: column;
  }

  .search-box {
    min-width: 0;
  }

  .sort-box {
    min-width: 0;
  }

  .spo-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .spo-name {
    max-width: 100%;
  }

  .specialty-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .specialty-stats {
    padding-left: 0;
    width: 100%;
  }

  .spo-progress {
    padding: 10px 16px;
  }

  .specialties-list {
    padding: 8px 16px 12px;
  }
}

/* Small Mobile: < 480px */
@media (max-width: 479px) {
  .page-title {
    font-size: 20px;
    margin-bottom: 16px;
  }

  .summary-section {
    padding: 16px;
  }

  .quick-stat-value {
    font-size: 22px;
  }

  .quick-stat-card {
    padding: 12px;
  }

  .spo-header {
    padding: 12px 14px;
  }

  .spo-progress {
    padding: 8px 14px;
  }

  .specialties-list {
    padding: 6px 14px 10px;
  }

  .specialty-code {
    min-width: auto;
  }

  .stat-available {
    min-width: auto;
  }
}
</style>
