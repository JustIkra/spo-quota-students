<script setup>
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

const props = defineProps({
  spoList: {
    type: Array,
    required: true
  }
})

function shortName(name) {
  // Извлечь имя из кавычек: «Название» или "Название"
  const quoted = name.match(/[«""]([^»""]+)[»""]/)
  if (quoted) return quoted[1]
  // Убрать типовой префикс
  const stripped = name.replace(
    /^(государственное|бюджетное|профессиональное|образовательное|учреждение|автономное|казённое|муниципальное|среднего|профессионального|образования)\s+/gi,
    ''
  )
  if (stripped !== name && stripped.length > 0) return stripped
  return name
}

const sortedList = computed(() =>
  [...props.spoList].sort((a, b) => a.spo_name.localeCompare(b.spo_name))
)

const shortNames = computed(() =>
  sortedList.value.map(s => {
    const short = shortName(s.spo_name)
    return short.length > 20 ? short.slice(0, 18) + '…' : short
  })
)

const chartOptions = computed(() => ({
  chart: {
    type: 'area',
    height: 300,
    toolbar: { show: false },
    zoom: { enabled: false }
  },
  stroke: {
    curve: 'smooth',
    width: 2
  },
  fill: {
    type: 'gradient',
    gradient: {
      opacityFrom: 0.4,
      opacityTo: 0.05
    }
  },
  colors: ['#6b7280', '#2563eb'],
  xaxis: {
    categories: shortNames.value,
    labels: {
      show: false
    },
    tooltip: { enabled: false }
  },
  yaxis: {
    min: 0,
    labels: {
      style: { fontSize: '12px' }
    }
  },
  legend: {
    position: 'top',
    horizontalAlign: 'left',
    fontSize: '13px'
  },
  tooltip: {
    shared: true,
    x: {
      formatter(val, { dataPointIndex }) {
        return sortedList.value[dataPointIndex]?.spo_name || val
      }
    },
    y: {
      formatter(val) {
        return val + ' чел.'
      }
    }
  },
  grid: {
    borderColor: '#e5e7eb',
    strokeDashArray: 4
  },
  dataLabels: {
    enabled: false
  }
}))

const series = computed(() => [
  {
    name: 'Квота',
    data: sortedList.value.map(s => s.total_quota)
  },
  {
    name: 'Студенты',
    data: sortedList.value.map(s => s.total_students)
  }
])
</script>

<template>
  <div class="chart-card">
    <h2 class="chart-title">Квоты и набор по учреждениям</h2>
    <VueApexCharts
      type="area"
      :height="300"
      :options="chartOptions"
      :series="series"
    />
  </div>
</template>

<style scoped>
.chart-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 24px;
  margin-top: 32px;
}

.chart-title {
  font-size: 20px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16px;
}

@media (max-width: 767px) {
  .chart-card {
    padding: 16px;
  }

  .chart-title {
    font-size: 18px;
  }
}

@media (max-width: 479px) {
  .chart-card {
    padding: 12px;
  }

  .chart-title {
    font-size: 16px;
  }
}
</style>
