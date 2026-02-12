<script setup lang="ts">
import { ArrowLeft, Download, Loader2, Pause, Play, RefreshCw, Settings, Trash2 } from 'lucide-vue-next'
import { formatTimestamp } from '~/lib/utils'

const route = useRoute()
const api = useApi()
const deviceId = computed(() => Number(route.params.id))

const device = ref<any>(null)
const stats = ref<any>(null)
const graphData = ref<any[]>([])
const loading = ref(true)
const rescanning = ref(false)

const timeRange = ref('1h')
const timeRanges = [
  { value: '1h', label: '1 Hour', seconds: 3600 },
  { value: '6h', label: '6 Hours', seconds: 21600 },
  { value: '12h', label: '12 Hours', seconds: 43200 },
  { value: '24h', label: '24 Hours', seconds: 86400 },
  { value: '48h', label: '48 Hours', seconds: 172800 },
]

const showSettings = ref(false)
const settingsForm = reactive({
  name: '',
  fingerprint_enabled: false,
  ping_type: 'icmp',
  interval_seconds: 1.0,
  packet_size: 64,
  retention_days: 14,
})

const retentionOptions = [1, 5, 7, 14, 30, 90]

async function fetchDevice() {
  try {
    device.value = await api.get(`/devices/${deviceId.value}`)
    settingsForm.name = device.value.name
    settingsForm.fingerprint_enabled = device.value.fingerprint_enabled
    settingsForm.ping_type = device.value.ping_type
    settingsForm.interval_seconds = device.value.interval_seconds
    settingsForm.packet_size = device.value.packet_size
    settingsForm.retention_days = device.value.retention_days
  } catch (e) {
    console.error('Failed to fetch device:', e)
  }
}

async function fetchStats() {
  try {
    stats.value = await api.get(`/stats/${deviceId.value}`)
  } catch (e) {
    console.error('Failed to fetch stats:', e)
  }
}

async function fetchGraph() {
  const range = timeRanges.find(r => r.value === timeRange.value)
  if (!range) return
  const now = Date.now() / 1000
  try {
    const data = await api.get<any>(`/stats/${deviceId.value}/graph?start=${now - range.seconds}&end=${now}`)
    graphData.value = data.points || []
  } catch (e) {
    console.error('Failed to fetch graph:', e)
  }
}

async function loadAll() {
  loading.value = true
  await Promise.all([fetchDevice(), fetchStats(), fetchGraph()])
  loading.value = false
}

let refreshInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  loadAll()
  refreshInterval = setInterval(() => {
    fetchStats()
    fetchGraph()
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})

watch(timeRange, () => {
  fetchGraph()
})

async function toggleMonitoring() {
  try {
    device.value = await api.post(`/devices/${deviceId.value}/toggle`)
  } catch (e) {
    console.error('Failed to toggle:', e)
  }
}

async function rescan() {
  rescanning.value = true
  try {
    await api.post(`/devices/${deviceId.value}/rescan`)
    setTimeout(async () => {
      await fetchDevice()
      rescanning.value = false
    }, 5000)
  } catch (e) {
    rescanning.value = false
    console.error('Failed to rescan:', e)
  }
}

async function saveSettings() {
  try {
    device.value = await api.put(`/devices/${deviceId.value}`, { ...settingsForm })
    showSettings.value = false
  } catch (e) {
    console.error('Failed to save settings:', e)
  }
}

function exportCsv() {
  const range = timeRanges.find(r => r.value === timeRange.value)
  if (!range) return
  const now = Date.now() / 1000
  window.open(`/api/stats/${deviceId.value}/export?start=${now - range.seconds}&end=${now}`, '_blank')
}

const clearing = ref(false)

async function clearData() {
  if (!confirm('Are you sure you want to delete all ping data for this device? This cannot be undone.')) return
  clearing.value = true
  try {
    await api.del(`/stats/${deviceId.value}/data`)
    graphData.value = []
    await fetchStats()
  } catch (e) {
    console.error('Failed to clear data:', e)
  } finally {
    clearing.value = false
  }
}
</script>

<template>
  <div v-if="loading" class="flex items-center justify-center py-20">
    <Loader2 class="h-8 w-8 animate-spin text-primary" />
  </div>

  <div v-else-if="device" class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex items-center gap-4">
        <NuxtLink to="/" class="flex h-9 w-9 items-center justify-center rounded-lg border border-border hover:bg-accent transition-colors">
          <ArrowLeft class="h-4 w-4" />
        </NuxtLink>
        <div>
          <div class="flex items-center gap-3">
            <h1 class="text-2xl font-bold">{{ device.name }}</h1>
            <StatusBadge :status="device.monitoring_enabled ? device.status : 'unknown'" />
          </div>
          <p class="text-sm text-muted-foreground">
            {{ device.ip_address }}
            <span v-if="device.manufacturer"> &middot; {{ device.manufacturer }}</span>
          </p>
        </div>
      </div>
      <div class="flex gap-2">
        <button
          class="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-medium hover:bg-accent transition-colors"
          @click="rescan"
          :disabled="rescanning"
        >
          <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': rescanning }" />
          Re-scan
        </button>
        <button
          class="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-medium hover:bg-accent transition-colors"
          @click="toggleMonitoring"
        >
          <Pause v-if="device.monitoring_enabled" class="h-4 w-4" />
          <Play v-else class="h-4 w-4" />
          {{ device.monitoring_enabled ? 'Pause' : 'Resume' }}
        </button>
        <button
          class="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-medium hover:bg-accent transition-colors"
          @click="showSettings = !showSettings"
        >
          <Settings class="h-4 w-4" />
          Settings
        </button>
        <button
          class="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-medium hover:bg-accent transition-colors"
          @click="exportCsv"
        >
          <Download class="h-4 w-4" />
          Export
        </button>
        <button
          class="flex items-center gap-2 rounded-lg border border-red-500/30 px-3 py-2 text-sm font-medium text-red-500 hover:bg-red-500/10 transition-colors"
          :disabled="clearing"
          @click="clearData"
        >
          <Loader2 v-if="clearing" class="h-4 w-4 animate-spin" />
          <Trash2 v-else class="h-4 w-4" />
          Clear Data
        </button>
      </div>
    </div>

    <!-- Settings panel -->
    <div v-if="showSettings" class="rounded-xl border border-border bg-card p-5">
      <h3 class="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">Device Settings</h3>
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <label class="mb-1.5 block text-sm font-medium">Name</label>
          <input v-model="settingsForm.name" type="text" class="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring" />
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium">Ping Type</label>
          <select v-model="settingsForm.ping_type" class="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring">
            <option value="icmp">ICMP</option>
            <option value="arp">ARP</option>
            <option value="both">Both</option>
          </select>
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium">Interval</label>
          <select v-model.number="settingsForm.interval_seconds" class="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring">
            <option :value="1.0">1s</option>
            <option :value="0.1">0.1s</option>
            <option :value="0.01">0.01s</option>
          </select>
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium">Packet Size</label>
          <select v-model.number="settingsForm.packet_size" class="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring">
            <option :value="64">64 B</option>
            <option :value="128">128 B</option>
            <option :value="256">256 B</option>
            <option :value="512">512 B</option>
            <option :value="1024">1 KB</option>
            <option :value="1500">1500 B</option>
          </select>
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium">Data Retention</label>
          <select v-model.number="settingsForm.retention_days" class="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring">
            <option v-for="d in retentionOptions" :key="d" :value="d">{{ d }} day{{ d > 1 ? 's' : '' }}</option>
          </select>
        </div>
        <div class="flex items-end">
          <label class="flex items-center gap-3 cursor-pointer">
            <div class="relative">
              <input
                v-model="settingsForm.fingerprint_enabled"
                type="checkbox"
                class="peer sr-only"
              />
              <div class="h-5 w-9 rounded-full bg-muted transition-colors peer-checked:bg-primary"></div>
              <div class="absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition-transform peer-checked:translate-x-4"></div>
            </div>
            <div>
              <span class="text-sm font-medium">OS Fingerprinting</span>
              <p class="text-xs text-muted-foreground">Full port scan + OS detection. May trigger firewall alerts.</p>
            </div>
          </label>
        </div>
      </div>
      <div class="mt-4 flex justify-end">
        <button
          class="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          @click="saveSettings"
        >
          Save Changes
        </button>
      </div>
    </div>

    <!-- Stats cards -->
    <StatsCards :stats="stats" />

    <!-- Device info -->
    <DeviceInfo :device="device" />

    <!-- Graph -->
    <div>
      <div class="mb-3 flex items-center justify-between">
        <h3 class="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Latency & Packet Loss</h3>
        <div class="flex gap-1">
          <button
            v-for="r in timeRanges"
            :key="r.value"
            class="rounded-md px-2.5 py-1 text-xs font-medium transition-colors"
            :class="timeRange === r.value ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-accent'"
            @click="timeRange = r.value"
          >
            {{ r.label }}
          </button>
        </div>
      </div>
      <LatencyChart :points="graphData" :ping-type="device.ping_type" />
    </div>

    <!-- Raw nmap output -->
    <div v-if="device.nmap_raw" class="rounded-xl border border-border bg-card p-5">
      <h3 class="mb-3 text-sm font-semibold uppercase tracking-wider text-muted-foreground">Raw nmap Output</h3>
      <pre class="max-h-60 overflow-auto rounded-lg bg-muted/50 p-4 text-xs font-mono text-muted-foreground">{{ JSON.parse(device.nmap_raw)?.raw || 'No data' }}</pre>
    </div>
  </div>
</template>
