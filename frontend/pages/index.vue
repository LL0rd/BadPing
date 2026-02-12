<script setup lang="ts">
import { Plus, Radar, RefreshCw } from 'lucide-vue-next'

const { devices, loading, fetchDevices, toggleMonitoring, deleteDevice } = useDevices()
const showAddDialog = ref(false)
const showDiscoverDialog = ref(false)
const api = useApi()

let refreshInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  fetchDevices()
  refreshInterval = setInterval(fetchDevices, 5000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})

async function handleDiscover(device: any) {
  try {
    await api.post('/devices', {
      name: device.hostname || device.ip_address,
      ip_address: device.ip_address,
      mac_address: device.mac_address || null,
      ping_type: 'icmp',
      interval_seconds: 1.0,
      packet_size: 64,
    })
    await fetchDevices()
  } catch (e) {
    console.error('Failed to add discovered device:', e)
  }
}

async function handleToggle(id: number) {
  await toggleMonitoring(id)
}

async function handleDelete(id: number) {
  if (confirm('Delete this device and all its monitoring data?')) {
    await deleteDevice(id)
  }
}
</script>

<template>
  <div>
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">Dashboard</h1>
        <p class="text-sm text-muted-foreground">Monitor your network devices in real-time</p>
      </div>
      <div class="flex gap-2">
        <button
          class="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-medium hover:bg-accent transition-colors"
          @click="fetchDevices"
        >
          <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': loading }" />
          Refresh
        </button>
        <button
          class="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-medium hover:bg-accent transition-colors"
          @click="showDiscoverDialog = true"
        >
          <Radar class="h-4 w-4" />
          Scan Network
        </button>
        <button
          class="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          @click="showAddDialog = true"
        >
          <Plus class="h-4 w-4" />
          Add Device
        </button>
      </div>
    </div>

    <DeviceTable
      :devices="devices"
      :loading="loading"
      @toggle="handleToggle"
      @delete="handleDelete"
    />

    <AddDeviceDialog
      v-if="showAddDialog"
      @close="showAddDialog = false"
      @added="fetchDevices"
    />

    <DiscoverDialog
      v-if="showDiscoverDialog"
      @close="showDiscoverDialog = false"
      @add-device="handleDiscover"
    />
  </div>
</template>
