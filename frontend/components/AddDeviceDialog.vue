<script setup lang="ts">
import { Check, Loader2, Search, X } from 'lucide-vue-next'

const emit = defineEmits<{
  close: []
  added: []
}>()

const arpAvailable = inject<Ref<boolean>>('arpAvailable', ref(true))
const api = useApi()

const step = ref(1)
const loading = ref(false)
const checkResult = ref<any>(null)

const form = reactive({
  name: '',
  ip_address: '',
  mac_address: '',
  fingerprint_enabled: false,
  ping_type: 'icmp',
  interval_seconds: 1.0,
  packet_size: 64,
})

const intervals = [
  { value: 1.0, label: '1s' },
  { value: 0.1, label: '0.1s' },
  { value: 0.01, label: '0.01s' },
]

const packetSizes = [
  { value: 64, label: '64 B' },
  { value: 128, label: '128 B' },
  { value: 256, label: '256 B' },
  { value: 512, label: '512 B' },
  { value: 1024, label: '1 KB' },
  { value: 1500, label: '1500 B (MTU)' },
]

async function checkDevice() {
  loading.value = true
  try {
    checkResult.value = await api.post('/devices/check', {
      ip_address: form.ip_address || null,
      mac_address: form.mac_address || null,
    })
    step.value = 2
  } catch (e: any) {
    checkResult.value = { reachable: false, message: e.data?.detail || 'Check failed', same_subnet: true }
    step.value = 2
  } finally {
    loading.value = false
  }
}

async function addDevice() {
  loading.value = true
  try {
    await api.post('/devices', {
      ...form,
      ip_address: form.ip_address || null,
      mac_address: form.mac_address || null,
    })
    emit('added')
    emit('close')
  } catch (e) {
    console.error('Failed to add device:', e)
  } finally {
    loading.value = false
  }
}

const arpDisabled = computed(() => {
  return !arpAvailable.value || (checkResult.value && !checkResult.value.same_subnet)
})

const arpBlocked = computed(() => {
  return arpDisabled.value && (form.ping_type === 'arp' || form.ping_type === 'both')
})
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="emit('close')">
    <div class="w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-2xl">
      <div class="mb-5 flex items-center justify-between">
        <h2 class="text-lg font-semibold">Add Device</h2>
        <button class="text-muted-foreground hover:text-foreground" @click="emit('close')">
          <X class="h-5 w-5" />
        </button>
      </div>

      <!-- Step 1: Enter IP/MAC and check -->
      <div v-if="step === 1" class="space-y-4">
        <div>
          <label class="mb-1.5 block text-sm font-medium">Device Name</label>
          <input
            v-model="form.name"
            type="text"
            placeholder="e.g. Main Router"
            class="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium">IP Address</label>
          <input
            v-model="form.ip_address"
            type="text"
            placeholder="e.g. 192.168.1.1"
            class="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm font-mono outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium">MAC Address <span class="text-muted-foreground">(optional)</span></label>
          <input
            v-model="form.mac_address"
            type="text"
            placeholder="e.g. AA:BB:CC:DD:EE:FF"
            class="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm font-mono outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <button
          class="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
          :disabled="!form.name || (!form.ip_address && !form.mac_address) || loading"
          @click="checkDevice"
        >
          <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
          <Search v-else class="h-4 w-4" />
          Check Reachability
        </button>
      </div>

      <!-- Step 2: Check result + configure ping settings -->
      <div v-if="step === 2" class="space-y-4">
        <div
          class="rounded-lg border p-3 text-sm"
          :class="checkResult?.reachable ? 'border-green-500/30 bg-green-500/10 text-green-500' : 'border-yellow-500/30 bg-yellow-500/10 text-yellow-500'"
        >
          <div class="flex items-center gap-2">
            <Check v-if="checkResult?.reachable" class="h-4 w-4" />
            <span>{{ checkResult?.message }}</span>
          </div>
          <p v-if="!checkResult?.same_subnet" class="mt-1 text-xs opacity-80">
            This device is on a different subnet. ARP ping will not work.
          </p>
        </div>

        <div>
          <label class="mb-1.5 block text-sm font-medium">Ping Type</label>
          <div class="flex gap-2">
            <button
              v-for="opt in ['icmp', 'arp', 'both']"
              :key="opt"
              class="flex-1 rounded-lg border px-3 py-2 text-sm font-medium uppercase transition-colors"
              :class="form.ping_type === opt
                ? 'border-primary bg-primary/10 text-primary'
                : 'border-border hover:bg-accent'"
              :disabled="(opt === 'arp' || opt === 'both') && arpDisabled"
              @click="form.ping_type = opt"
            >
              {{ opt }}
            </button>
          </div>
          <p v-if="!arpAvailable" class="mt-1 text-xs text-yellow-500">
            ARP ping unavailable: requires root privileges (Docker with NET_RAW/NET_ADMIN).
          </p>
          <p v-else-if="checkResult && !checkResult.same_subnet" class="mt-1 text-xs text-yellow-500">
            ARP ping is blocked: device is on a different subnet.
          </p>
        </div>

        <div>
          <label class="mb-1.5 block text-sm font-medium">Ping Interval</label>
          <div class="flex gap-2">
            <button
              v-for="opt in intervals"
              :key="opt.value"
              class="flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition-colors"
              :class="form.interval_seconds === opt.value
                ? 'border-primary bg-primary/10 text-primary'
                : 'border-border hover:bg-accent'"
              @click="form.interval_seconds = opt.value"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>

        <div>
          <label class="mb-1.5 block text-sm font-medium">Packet Size</label>
          <select
            v-model.number="form.packet_size"
            class="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
          >
            <option v-for="opt in packetSizes" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>

        <div>
          <label class="flex items-center gap-3 cursor-pointer">
            <div class="relative">
              <input
                v-model="form.fingerprint_enabled"
                type="checkbox"
                class="peer sr-only"
              />
              <div class="h-5 w-9 rounded-full bg-muted transition-colors peer-checked:bg-primary"></div>
              <div class="absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition-transform peer-checked:translate-x-4"></div>
            </div>
            <span class="text-sm font-medium">Enable OS Fingerprinting</span>
          </label>
          <p class="mt-1 text-xs text-yellow-500">
            Runs a full port scan with OS detection. May trigger firewall alerts.
          </p>
        </div>

        <div class="flex gap-2">
          <button
            class="flex-1 rounded-lg border border-border px-4 py-2.5 text-sm font-medium hover:bg-accent transition-colors"
            @click="step = 1"
          >
            Back
          </button>
          <button
            class="flex flex-1 items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
            :disabled="loading || arpBlocked"
            @click="addDevice"
          >
            <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
            Add Device
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
