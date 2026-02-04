<script setup>
import { computed } from 'vue'
import { useRouter, RouterView, RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const navItems = computed(() => {
  if (auth.isAdmin) {
    return [
      { to: '/admin', label: 'Главная' },
      { to: '/admin/spo', label: 'Учреждения' },
      { to: '/admin/operators', label: 'Операторы' },
      { to: '/admin/quotas', label: 'Квоты' },
      { to: '/admin/stats', label: 'Статистика' }
    ]
  }
  return [
    { to: '/operator', label: 'Главная' },
    { to: '/operator/specialties', label: 'Специальности' },
    { to: '/operator/students', label: 'Студенты' },
    { to: '/operator/stats', label: 'Статистика' }
  ]
})

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="layout">
    <header class="header">
      <div class="header-content">
        <div class="logo">Система учета квот</div>
        <nav class="nav">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="nav-link"
            active-class="nav-link-active"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
        <div class="user-info">
          <span class="user-name">{{ auth.user?.login }}</span>
          <span class="user-role">({{ auth.isAdmin ? 'Администратор' : 'Оператор' }})</span>
          <button class="logout-btn" @click="logout">Выйти</button>
        </div>
      </div>
    </header>
    <main class="main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
  gap: 32px;
}

.logo {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
}

.nav {
  display: flex;
  gap: 8px;
  flex: 1;
}

.nav-link {
  padding: 8px 16px;
  color: #6b7280;
  text-decoration: none;
  border-radius: 6px;
  transition: background-color 0.2s, color 0.2s;
}

.nav-link:hover {
  background-color: #f3f4f6;
  color: #374151;
  text-decoration: none;
}

.nav-link-active {
  background-color: #eff6ff;
  color: #2563eb;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-weight: 500;
  color: #374151;
}

.user-role {
  color: #6b7280;
  font-size: 13px;
}

.logout-btn {
  margin-left: 8px;
  padding: 6px 12px;
  font-size: 13px;
  color: #dc2626;
  background: none;
  border: 1px solid #dc2626;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}

.logout-btn:hover {
  background-color: #dc2626;
  color: white;
}

.main {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 20px;
  width: 100%;
}
</style>
