<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { adminApi } from '../../api/admin'
import { statsApi } from '../../api/stats'

const spoCount = ref(0)
const operatorCount = ref(0)
const studentCount = ref(0)
const loading = ref(true)

onMounted(async () => {
  try {
    const [spoList, operators, stats] = await Promise.all([
      adminApi.getSpoList(),
      adminApi.getOperators(),
      statsApi.getStats()
    ])
    spoCount.value = spoList.length
    operatorCount.value = operators.length
    studentCount.value = stats.reduce((sum, item) => sum + item.enrolled, 0)
  } catch (error) {
    console.error('Ошибка загрузки данных:', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="dashboard">
    <h1 class="page-title">Панель администратора</h1>

    <div v-if="loading" class="loading">Загрузка...</div>

    <div v-else class="stats-grid">
      <RouterLink to="/admin/spo" class="stat-card">
        <div class="stat-value">{{ spoCount }}</div>
        <div class="stat-label">Учреждений</div>
      </RouterLink>

      <RouterLink to="/admin/operators" class="stat-card">
        <div class="stat-value">{{ operatorCount }}</div>
        <div class="stat-label">Операторов</div>
      </RouterLink>

      <RouterLink to="/admin/stats" class="stat-card">
        <div class="stat-value">{{ studentCount }}</div>
        <div class="stat-label">Студентов</div>
      </RouterLink>
    </div>

    <div class="quick-links">
      <h2 class="section-title">Быстрые действия</h2>
      <div class="links-grid">
        <RouterLink to="/admin/spo" class="link-card">
          Управление учреждениями
        </RouterLink>
        <RouterLink to="/admin/operators" class="link-card">
          Управление операторами
        </RouterLink>
        <RouterLink to="/admin/quotas" class="link-card">
          Настройка квот
        </RouterLink>
        <RouterLink to="/admin/stats" class="link-card">
          Просмотр статистики
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 900px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 32px;
}

.loading {
  text-align: center;
  color: #6b7280;
  padding: 40px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  text-decoration: none;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  text-decoration: none;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: #2563eb;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16px;
}

.links-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.link-card {
  display: block;
  padding: 16px 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  color: #374151;
  text-decoration: none;
  transition: background-color 0.2s;
}

.link-card:hover {
  background-color: #f9fafb;
  text-decoration: none;
}

/* Mobile: 480px - 767px */
@media (max-width: 767px) {
  .page-title {
    font-size: 22px;
    margin-bottom: 24px;
    word-break: break-word;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .links-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Small Mobile: < 480px */
@media (max-width: 479px) {
  .page-title {
    font-size: 20px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .stat-value {
    font-size: 28px;
  }

  .stat-card {
    padding: 16px;
  }

  .links-grid {
    grid-template-columns: 1fr;
  }
}
</style>
