<script setup>
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

const props = defineProps({
  specialties: {
    type: Array,
    required: true
  }
})

const sorted = computed(() =>
  [...props.specialties].sort((a, b) => (a.code || '').localeCompare(b.code || ''))
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
    categories: sorted.value.map(s => s.code || s.name),
    labels: {
      style: { fontSize: '12px' }
    }
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
    intersect: false,
    x: {
      formatter(val, opts) {
        const spec = sorted.value[opts.dataPointIndex]
        return spec ? spec.code + ' - ' + spec.name : val
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

const series = computed(() => {
  const data = sorted.value
  return [
    {
      name: 'Квота',
      data: data.map(s => s.quota != null ? s.quota : 0)
    },
    {
      name: 'Записано',
      data: data.map(s => s.students_count != null ? s.students_count : 0)
    }
  ]
})
</script>

<template>
  <div class="chart-card">
    <h2 class="chart-title">Квоты и набор по направлениям</h2>
    <VueApexCharts
      type="area"
      height="300"
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
