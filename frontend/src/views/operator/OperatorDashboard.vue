<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { operatorApi } from '../../api/operator'
import { statsApi } from '../../api/stats'

const auth = useAuthStore()

const specialtyCount = ref(0)
const studentCount = ref(0)
const loading = ref(true)

onMounted(async () => {
  try {
    const [specialties, stats] = await Promise.all([
      operatorApi.getSpecialties(),
      statsApi.getStats()
    ])
    specialtyCount.value = specialties.length
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
    <h1 class="page-title">Панель оператора</h1>
    <p class="spo-name" v-if="auth.user?.spo_name">
      Учреждение: {{ auth.user.spo_name }}
    </p>

    <div v-if="loading" class="loading">Загрузка...</div>

    <div v-else class="stats-grid">
      <RouterLink to="/operator/specialties" class="stat-card">
        <div class="stat-value">{{ specialtyCount }}</div>
        <div class="stat-label">Направлений</div>
      </RouterLink>

      <RouterLink to="/operator/students" class="stat-card">
        <div class="stat-value">{{ studentCount }}</div>
        <div class="stat-label">Студентов</div>
      </RouterLink>
    </div>

    <div class="quick-links">
      <h2 class="section-title">Быстрые действия</h2>
      <div class="links-grid">
        <RouterLink to="/operator/specialties" class="link-card">
          Управление направлениями
        </RouterLink>
        <RouterLink to="/operator/students" class="link-card">
          Список студентов
        </RouterLink>
        <RouterLink to="/operator/stats" class="link-card">
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
  margin-bottom: 8px;
}

.spo-name {
  color: #6b7280;
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
</style>
