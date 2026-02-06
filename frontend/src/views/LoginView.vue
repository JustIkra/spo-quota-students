<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AppInput from '../components/ui/AppInput.vue'
import AppButton from '../components/ui/AppButton.vue'

const router = useRouter()
const auth = useAuthStore()

const form = ref({
  login: '',
  password: ''
})
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''

  if (!form.value.login || !form.value.password) {
    error.value = 'Заполните все поля'
    return
  }

  loading.value = true

  try {
    await auth.login(form.value.login, form.value.password)
    router.push(auth.isAdmin ? '/admin' : '/operator')
  } catch (e) {
    if (e.response?.status === 401) {
      error.value = 'Неверный логин или пароль'
    } else {
      error.value = 'Ошибка подключения к серверу'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="title">Система учета квот</h1>
      <p class="subtitle">Вход в систему</p>

      <form class="form" @submit.prevent="submit">
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <AppInput
          v-model="form.login"
          label="Логин"
          placeholder="Введите логин"
          required
        />

        <AppInput
          v-model="form.password"
          type="password"
          label="Пароль"
          placeholder="Введите пароль"
          required
        />

        <AppButton
          type="submit"
          :loading="loading"
          class="submit-btn"
        >
          Войти
        </AppButton>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background-color: #f5f5f5;
}

.login-card {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.title {
  font-size: 24px;
  font-weight: 600;
  color: #111827;
  text-align: center;
  margin-bottom: 8px;
}

.subtitle {
  color: #6b7280;
  text-align: center;
  margin-bottom: 32px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.error-message {
  padding: 12px;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #dc2626;
  font-size: 14px;
  text-align: center;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  font-size: 16px;
  margin-top: 8px;
}

/* Small Mobile: < 480px */
@media (max-width: 479px) {
  .login-card {
    padding: 24px;
  }

  .title {
    font-size: 20px;
  }

  .subtitle {
    margin-bottom: 24px;
  }

  .form {
    gap: 16px;
  }
}
</style>
