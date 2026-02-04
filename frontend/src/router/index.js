import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true }
  },
  {
    path: '/',
    component: () => import('../components/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      // Админские маршруты
      {
        path: '',
        redirect: to => {
          const auth = useAuthStore()
          return auth.isAdmin ? '/admin' : '/operator'
        }
      },
      {
        path: 'admin',
        name: 'admin-dashboard',
        component: () => import('../views/admin/AdminDashboard.vue'),
        meta: { role: 'admin' }
      },
      {
        path: 'admin/spo',
        name: 'spo-list',
        component: () => import('../views/admin/SpoList.vue'),
        meta: { role: 'admin' }
      },
      {
        path: 'admin/operators',
        name: 'operator-list',
        component: () => import('../views/admin/OperatorList.vue'),
        meta: { role: 'admin' }
      },
      {
        path: 'admin/quotas',
        name: 'quota-settings',
        component: () => import('../views/admin/QuotaSettings.vue'),
        meta: { role: 'admin' }
      },
      {
        path: 'admin/stats',
        name: 'admin-stats',
        component: () => import('../views/admin/AdminStats.vue'),
        meta: { role: 'admin' }
      },
      // Операторские маршруты
      {
        path: 'operator',
        name: 'operator-dashboard',
        component: () => import('../views/operator/OperatorDashboard.vue'),
        meta: { role: 'operator' }
      },
      {
        path: 'operator/specialties',
        name: 'specialty-list',
        component: () => import('../views/operator/SpecialtyList.vue'),
        meta: { role: 'operator' }
      },
      {
        path: 'operator/students',
        name: 'student-list',
        component: () => import('../views/operator/StudentList.vue'),
        meta: { role: 'operator' }
      },
      {
        path: 'operator/stats',
        name: 'operator-stats',
        component: () => import('../views/operator/OperatorStats.vue'),
        meta: { role: 'operator' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  // Инициализация при первом входе
  if (!auth.user && auth.token) {
    try {
      await auth.init()
    } catch {
      // Ошибка авторизации, продолжаем
    }
  }

  // Страницы для гостей
  if (to.meta.guest) {
    if (auth.isAuthenticated) {
      return next(auth.isAdmin ? '/admin' : '/operator')
    }
    return next()
  }

  // Защищенные страницы
  if (to.meta.requiresAuth) {
    if (!auth.isAuthenticated) {
      return next('/login')
    }

    // Проверка роли
    if (to.meta.role === 'admin' && !auth.isAdmin) {
      return next('/operator')
    }
    if (to.meta.role === 'operator' && !auth.isOperator) {
      return next('/admin')
    }
  }

  next()
})

export default router
