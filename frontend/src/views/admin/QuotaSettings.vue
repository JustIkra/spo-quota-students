<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '../../api/admin'
import { statsApi } from '../../api/stats'
import AppButton from '../../components/ui/AppButton.vue'
import AppInput from '../../components/ui/AppInput.vue'
import AppTable from '../../components/ui/AppTable.vue'

const settings = ref({ base_quota: 0 })
const specialties = ref([])
const loading = ref(true)
const savingSettings = ref(false)
const editingQuota = ref(null)
const quotaValue = ref('')

const columns = [
  { key: 'spo_name', label: 'СПО' },
  { key: 'code', label: 'Код' },
  { key: 'name', label: 'Название' },
  { key: 'quota', label: 'Квота', width: '100px' },
  { key: 'enrolled', label: 'Записано', width: '100px' },
  { key: 'actions', label: 'Действия', width: '180px' }
]

onMounted(() => {
  loadData()
})

async function loadData() {
  loading.value = true
  try {
    const [settingsData, statsData] = await Promise.all([
      adminApi.getSettings(),
      statsApi.getStats()
    ])
    settings.value = settingsData
    specialties.value = statsData
  } catch (error) {
    console.error('Ошибка загрузки:', error)
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  savingSettings.value = true
  try {
    await adminApi.updateSettings({ base_quota: Number(settings.value.base_quota) })
    alert('Настройки сохранены')
  } catch (error) {
    console.error('Ошибка сохранения:', error)
    alert('Ошибка сохранения: ' + (error.response?.data?.detail || 'Неизвестная ошибка'))
  } finally {
    savingSettings.value = false
  }
}

function startEditQuota(specialty) {
  editingQuota.value = specialty.specialty_id
  quotaValue.value = specialty.quota?.toString() || ''
}

function cancelEditQuota() {
  editingQuota.value = null
  quotaValue.value = ''
}

async function saveQuota(specialty) {
  try {
    const quota = quotaValue.value ? Number(quotaValue.value) : null
    await adminApi.updateSpecialtyQuota(specialty.specialty_id, quota)
    editingQuota.value = null
    await loadData()
  } catch (error) {
    console.error('Ошибка сохранения квоты:', error)
    alert('Ошибка: ' + (error.response?.data?.detail || 'Неизвестная ошибка'))
  }
}
</script>

<template>
  <div class="quota-settings">
    <h1 class="page-title">Настройка квот</h1>

    <div class="settings-section">
      <h2 class="section-title">Базовая квота по умолчанию</h2>
      <div class="default-quota-form">
        <AppInput
          v-model="settings.base_quota"
          type="number"
          label="Квота по умолчанию для новых специальностей"
          placeholder="0"
        />
        <AppButton :loading="savingSettings" @click="saveSettings">
          Сохранить
        </AppButton>
      </div>
    </div>

    <div class="specialties-section">
      <h2 class="section-title">Квоты по специальностям</h2>
      <p class="section-hint">
        Если квота не задана, используется значение по умолчанию ({{ settings.base_quota }}).
      </p>

      <AppTable
        :columns="columns"
        :data="specialties"
        :loading="loading"
        empty-text="Нет специальностей"
      >
        <template #quota="{ row }">
          <template v-if="editingQuota === row.specialty_id">
            <input
              v-model="quotaValue"
              type="number"
              class="quota-input"
              placeholder="По умолч."
            />
          </template>
          <template v-else>
            {{ row.quota ?? `${settings.base_quota} (по умолч.)` }}
          </template>
        </template>
        <template #actions="{ row }">
          <div class="actions">
            <template v-if="editingQuota === row.specialty_id">
              <AppButton variant="primary" @click="saveQuota(row)">
                Сохранить
              </AppButton>
              <AppButton variant="secondary" @click="cancelEditQuota">
                Отмена
              </AppButton>
            </template>
            <template v-else>
              <AppButton variant="secondary" @click="startEditQuota(row)">
                Изменить
              </AppButton>
            </template>
          </div>
        </template>
      </AppTable>
    </div>
  </div>
</template>

<style scoped>
.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 32px;
}

.settings-section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 32px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 16px 0;
}

.section-hint {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 16px;
}

.default-quota-form {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  max-width: 400px;
}

.default-quota-form > :first-child {
  flex: 1;
}

.specialties-section {
  margin-top: 24px;
}

.quota-input {
  width: 100px;
  padding: 6px 10px;
  font-size: 14px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
}

.actions {
  display: flex;
  gap: 8px;
}
</style>
