<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  columns: {
    type: Array,
    required: true
    // [{ key: 'id', label: 'ID', width: '80px' }]
  },
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  emptyText: {
    type: String,
    default: 'Нет данных'
  },
  pageSize: {
    type: Number,
    default: 0 // 0 = no pagination
  }
})

const currentPage = ref(1)

watch(() => props.data.length, () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = Math.max(1, totalPages.value)
  }
})

const totalPages = computed(() => {
  if (!props.pageSize || props.data.length === 0) return 1
  return Math.ceil(props.data.length / props.pageSize)
})

const paginatedData = computed(() => {
  if (!props.pageSize) return props.data
  const start = (currentPage.value - 1) * props.pageSize
  return props.data.slice(start, start + props.pageSize)
})

const showPagination = computed(() => props.pageSize > 0 && totalPages.value > 1)

function goToPage(page) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

const visiblePages = computed(() => {
  const pages = []
  const total = totalPages.value
  const current = currentPage.value

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    if (current > 3) pages.push('...')
    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)
    for (let i = start; i <= end; i++) pages.push(i)
    if (current < total - 2) pages.push('...')
    pages.push(total)
  }
  return pages
})
</script>

<template>
  <div class="table-container">
    <!-- Desktop table -->
    <table class="table desktop-table">
      <thead>
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            :style="col.width ? { width: col.width } : {}"
          >
            {{ col.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td :colspan="columns.length" class="loading-cell">
            Загрузка...
          </td>
        </tr>
        <tr v-else-if="data.length === 0">
          <td :colspan="columns.length" class="empty-cell">
            {{ emptyText }}
          </td>
        </tr>
        <tr v-for="(row, index) in paginatedData" :key="row.id || index">
          <td v-for="col in columns" :key="col.key">
            <slot :name="col.key" :row="row" :value="row[col.key]">
              {{ row[col.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Mobile card layout -->
    <div class="mobile-cards">
      <div v-if="loading" class="loading-cell">Загрузка...</div>
      <div v-else-if="data.length === 0" class="empty-cell">{{ emptyText }}</div>
      <div v-else v-for="(row, index) in paginatedData" :key="row.id || index" class="mobile-card">
        <div
          v-for="col in columns"
          :key="col.key"
          class="mobile-card-row"
          :class="{ 'mobile-card-actions': col.key === 'actions' }"
        >
          <span v-if="col.key !== 'actions'" class="mobile-card-label">{{ col.label }}</span>
          <span v-if="col.key !== 'actions'" class="mobile-card-value">
            <slot :name="col.key" :row="row" :value="row[col.key]">
              {{ row[col.key] }}
            </slot>
          </span>
          <div v-else class="mobile-card-actions-content">
            <slot :name="col.key" :row="row" :value="row[col.key]">
              {{ row[col.key] }}
            </slot>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showPagination" class="pagination">
      <button
        class="page-btn"
        :disabled="currentPage === 1"
        @click="goToPage(currentPage - 1)"
      >
        &laquo;
      </button>
      <template v-for="(page, i) in visiblePages" :key="i">
        <span v-if="page === '...'" class="page-ellipsis">...</span>
        <button
          v-else
          class="page-btn"
          :class="{ active: page === currentPage }"
          @click="goToPage(page)"
        >
          {{ page }}
        </button>
      </template>
      <button
        class="page-btn"
        :disabled="currentPage === totalPages"
        @click="goToPage(currentPage + 1)"
      >
        &raquo;
      </button>
      <span class="page-info">{{ data.length }} записей</span>
    </div>
  </div>
</template>

<style scoped>
.table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.table th {
  font-weight: 600;
  color: #374151;
  background-color: #f9fafb;
}

.table tbody tr:hover {
  background-color: #f9fafb;
}

.table tbody tr:last-child td {
  border-bottom: none;
}

.loading-cell,
.empty-cell {
  text-align: center;
  color: #6b7280;
  padding: 32px 16px;
}

/* Mobile cards hidden by default */
.mobile-cards {
  display: none;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
}

.page-btn {
  min-width: 36px;
  height: 36px;
  padding: 0 8px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  color: #374151;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.page-btn:hover:not(:disabled):not(.active) {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.page-btn.active {
  background: #2563eb;
  border-color: #2563eb;
  color: white;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-ellipsis {
  min-width: 36px;
  text-align: center;
  color: #6b7280;
}

.page-info {
  margin-left: 12px;
  font-size: 13px;
  color: #6b7280;
}

/* Mobile: switch to card layout */
@media (max-width: 767px) {
  .desktop-table {
    display: none;
  }

  .mobile-cards {
    display: block;
  }

  .mobile-card {
    padding: 14px 16px;
    border-bottom: 1px solid #e5e7eb;
  }

  .mobile-card:last-child {
    border-bottom: none;
  }

  .mobile-card-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 4px 0;
  }

  .mobile-card-label {
    font-size: 12px;
    font-weight: 500;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    flex-shrink: 0;
    margin-right: 12px;
    padding-top: 1px;
  }

  .mobile-card-value {
    font-size: 14px;
    color: #111827;
    text-align: right;
    word-break: break-word;
  }

  .mobile-card-actions {
    justify-content: flex-end;
    padding-top: 10px;
    margin-top: 6px;
    border-top: 1px solid #f3f4f6;
  }

  .mobile-card-actions-content {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .pagination {
    padding: 10px 12px;
    flex-wrap: wrap;
  }

  .page-btn {
    min-width: 32px;
    height: 32px;
    font-size: 13px;
  }

  .page-ellipsis {
    min-width: 28px;
  }
}

/* Small Mobile: < 480px */
@media (max-width: 479px) {
  .mobile-card {
    padding: 12px;
  }

  .mobile-card-label {
    font-size: 11px;
  }

  .mobile-card-value {
    font-size: 13px;
  }

  .page-btn {
    min-width: 28px;
    height: 28px;
    font-size: 12px;
    padding: 0 4px;
  }

  .page-info {
    width: 100%;
    text-align: center;
    margin-left: 0;
    margin-top: 8px;
  }
}
</style>
