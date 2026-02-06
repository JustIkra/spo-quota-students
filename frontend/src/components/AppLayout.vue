<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute, RouterView, RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const menuOpen = ref(false)

const navItems = computed(() => {
  if (auth.isAdmin) {
    return [
      { to: '/admin', label: 'Главная' },
      { to: '/admin/spo', label: 'Учреждения' },
      { to: '/admin/operators', label: 'Операторы' },
      { to: '/admin/specialty-templates', label: 'Справочник' },
      { to: '/admin/specialties', label: 'Направления' },
      { to: '/admin/stats', label: 'Статистика' }
    ]
  }
  return [
    { to: '/operator', label: 'Главная' },
    { to: '/operator/specialties', label: 'Направления' },
    { to: '/operator/students', label: 'Студенты' },
    { to: '/operator/stats', label: 'Статистика' }
  ]
})

watch(() => route.path, () => {
  menuOpen.value = false
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
        <button class="hamburger" @click="menuOpen = !menuOpen" :class="{ open: menuOpen }">
          <span></span>
          <span></span>
          <span></span>
        </button>
        <nav class="nav" :class="{ 'nav-open': menuOpen }">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="nav-link"
            active-class="nav-link-active"
          >
            {{ item.label }}
          </RouterLink>
          <div class="user-info-mobile">
            <span class="user-name">{{ auth.user?.login }}</span>
            <span class="user-role">({{ auth.isAdmin ? 'Администратор' : 'Оператор' }})</span>
            <button class="logout-btn" @click="logout">Выйти</button>
          </div>
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
  gap: 16px;
}

.logo {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
  flex-shrink: 0;
}

.hamburger {
  display: none;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  margin-left: auto;
}

.hamburger span {
  display: block;
  width: 22px;
  height: 2px;
  background: #374151;
  border-radius: 1px;
  transition: transform 0.2s, opacity 0.2s;
}

.hamburger.open span:nth-child(1) {
  transform: translateY(7px) rotate(45deg);
}

.hamburger.open span:nth-child(2) {
  opacity: 0;
}

.hamburger.open span:nth-child(3) {
  transform: translateY(-7px) rotate(-45deg);
}

.nav {
  display: flex;
  gap: 8px;
  flex: 1;
}

.nav-link {
  padding: 8px 10px;
  color: #6b7280;
  text-decoration: none;
  border-radius: 6px;
  transition: background-color 0.2s, color 0.2s;
  white-space: nowrap;
  font-size: 13px;
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

.user-info-mobile {
  display: none;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  flex-shrink: 0;
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

/* Tablet and below: switch to hamburger menu */
@media (max-width: 1023px) {
  .header-content {
    flex-wrap: wrap;
    height: auto;
    padding: 12px 16px;
    gap: 12px;
  }

  .logo {
    font-size: 14px;
  }

  .hamburger {
    display: flex;
  }

  .nav {
    display: none;
    flex-direction: column;
    width: 100%;
    gap: 4px;
    padding-top: 12px;
    border-top: 1px solid #e5e7eb;
  }

  .nav.nav-open {
    display: flex;
  }

  .nav-link {
    padding: 10px 12px;
    font-size: 14px;
  }

  .user-info {
    display: none;
  }

  .user-info-mobile {
    display: flex;
    align-items: center;
    gap: 8px;
    padding-top: 12px;
    margin-top: 8px;
    border-top: 1px solid #e5e7eb;
    flex-wrap: wrap;
  }

  .main {
    padding: 20px 16px;
  }
}

/* Mobile */
@media (max-width: 767px) {
  .main {
    padding: 16px 12px;
  }
}

/* Small Mobile: < 480px */
@media (max-width: 479px) {
  .header-content {
    padding: 10px 12px;
  }

  .logo {
    font-size: 13px;
  }

  .main {
    padding: 12px;
  }
}
</style>
