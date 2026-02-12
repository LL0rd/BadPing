<script setup lang="ts">
import { AlertTriangle, Loader2, Radar, X } from 'lucide-vue-next'

const emit = defineEmits<{
  close: []
  addDevice: [device: any]
}>()

const arpAvailable = inject<Ref<boolean>>('arpAvailable', ref(true))
const api = useApi()
const loading = ref(false)
const subnet = ref('')
const discovered = ref<any[]>([])
const selected = ref<Set<string>>(new Set())

async function scan() {
  loading.value = true
  discovered.value = []
  selected.value = new Set()
  try {
    discovered.value = await api.post<any[]>('/devices/discover', {
      subnet: subnet.value || null,
    })
  } catch (e) {
    console.error('Discovery failed:', e)
  } finally {
    loading.value = false
  }
}

function toggleSelect(ip: string) {
  if (selected.value.has(ip)) {
    selected.value.delete(ip)
  } else {
    selected.value.add(ip)
  }
  selected.value = new Set(selected.value)
}

function addSelected() {
  for (const device of discovered.value) {
    if (selected.value.has(device.ip_address)) {
      emit('addDevice', device)
    }
  }
  emit('close')
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="emit('close')">
    <div class="w-full max-w-xl rounded-2xl border border-border bg-card p-6 shadow-2xl">
      <div class="mb-5 flex items-center justify-between">
        <h2 class="text-lg font-semibold">Discover Network Devices</h2>
        <button class="text-muted-foreground hover:text-foreground" @click="emit('close')">
          <X class="h-5 w-5" />
        </button>
      </div>

      <div v-if="!arpAvailable" class="mb-4 flex items-center gap-3 rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-3">
        <AlertTriangle class="h-5 w-5 shrink-0 text-yellow-500" />
        <p class="text-sm text-yellow-200">
          Network discovery requires root privileges. Run in Docker with <code class="rounded bg-yellow-500/20 px-1 py-0.5 text-xs">NET_RAW</code> / <code class="rounded bg-yellow-500/20 px-1 py-0.5 text-xs">NET_ADMIN</code> capabilities to enable ARP scanning.
        </p>
      </div>

      <div v-else class="mb-4 flex gap-2">
        <input
          v-model="subnet"
          type="text"
          placeholder="Subnet (auto-detect if empty)"
          class="flex-1 rounded-lg border border-input bg-background px-3 py-2 text-sm font-mono outline-none focus:ring-2 focus:ring-ring"
        />
        <button
          class="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          :disabled="loading"
          @click="scan"
        >
          <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
          <Radar v-else class="h-4 w-4" />
          Scan
        </button>
      </div>

      <div v-if="loading" class="py-12 text-center text-sm text-muted-foreground">
        <Loader2 class="mx-auto mb-2 h-6 w-6 animate-spin text-primary" />
        Scanning network... This may take a few seconds.
      </div>

      <div v-else-if="discovered.length > 0" class="max-h-80 overflow-y-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-border text-muted-foreground">
              <th class="px-3 py-2 text-left w-8"></th>
              <th class="px-3 py-2 text-left">IP Address</th>
              <th class="px-3 py-2 text-left">MAC Address</th>
              <th class="px-3 py-2 text-left">Manufacturer</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="d in discovered"
              :key="d.ip_address"
              class="border-b border-border/50 hover:bg-muted/30 cursor-pointer transition-colors"
              @click="toggleSelect(d.ip_address)"
            >
              <td class="px-3 py-2">
                <div
                  class="flex h-4 w-4 items-center justify-center rounded border"
                  :class="selected.has(d.ip_address) ? 'border-primary bg-primary' : 'border-border'"
                >
                  <svg v-if="selected.has(d.ip_address)" class="h-3 w-3 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </td>
              <td class="px-3 py-2 font-mono">{{ d.ip_address }}</td>
              <td class="px-3 py-2 font-mono text-xs text-muted-foreground">{{ d.mac_address || '-' }}</td>
              <td class="px-3 py-2 text-muted-foreground">{{ d.manufacturer || 'Unknown' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="py-8 text-center text-sm text-muted-foreground">
        Click "Scan" to discover devices on your network.
      </div>

      <div v-if="discovered.length > 0 && selected.size > 0" class="mt-4">
        <button
          class="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          @click="addSelected"
        >
          Add {{ selected.size }} device{{ selected.size > 1 ? 's' : '' }}
        </button>
      </div>
    </div>
  </div>
</template>
