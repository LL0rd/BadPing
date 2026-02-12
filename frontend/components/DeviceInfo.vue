<script setup lang="ts">
import { ChevronDown, ChevronUp, Cpu, Globe, Network, Server, Wifi } from 'lucide-vue-next'
import { formatTimestamp } from '~/lib/utils'

const props = defineProps<{
  device: any
}>()

const showAllGuesses = ref(false)

interface OsGuess {
  name: string
  confidence: number
}

const osGuesses = computed<OsGuess[]>(() => {
  const raw = props.device.os_info
  if (!raw) return []
  // Format: "Name1 (96%), Name2 (94%), ..."
  const matches = raw.matchAll(/([^,]+?)\s*\((\d+)%\)/g)
  const results: OsGuess[] = []
  for (const m of matches) {
    results.push({ name: m[1].trim(), confidence: parseInt(m[2]) })
  }
  // If no percentage pattern found, treat entire string as single entry
  if (results.length === 0 && raw.trim()) {
    results.push({ name: raw.trim(), confidence: 0 })
  }
  return results
})

const visibleGuesses = computed(() => {
  if (showAllGuesses.value) return osGuesses.value
  return osGuesses.value.slice(0, 5)
})

function confidenceColor(confidence: number): string {
  if (confidence >= 90) return 'bg-green-500/15 text-green-500 border-green-500/30'
  if (confidence >= 70) return 'bg-yellow-500/15 text-yellow-500 border-yellow-500/30'
  if (confidence >= 50) return 'bg-orange-500/15 text-orange-500 border-orange-500/30'
  if (confidence > 0) return 'bg-red-500/15 text-red-500 border-red-500/30'
  return 'bg-muted text-muted-foreground border-border'
}

const deviceTypes = computed<string[]>(() => {
  const raw = props.device.device_type
  if (!raw) return []
  return raw.split('|').map((t: string) => t.trim()).filter(Boolean)
})
</script>

<template>
  <div class="rounded-xl border border-border bg-card p-5">
    <h3 class="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">Device Information</h3>
    <div class="grid gap-4 sm:grid-cols-2">
      <div class="flex items-start gap-3">
        <Globe class="mt-0.5 h-4 w-4 text-muted-foreground" />
        <div>
          <div class="text-xs text-muted-foreground">IP Address</div>
          <div class="font-mono text-sm">{{ device.ip_address || '-' }}</div>
        </div>
      </div>
      <div class="flex items-start gap-3">
        <Network class="mt-0.5 h-4 w-4 text-muted-foreground" />
        <div>
          <div class="text-xs text-muted-foreground">MAC Address</div>
          <div class="font-mono text-sm">{{ device.mac_address || '-' }}</div>
        </div>
      </div>
      <div class="flex items-start gap-3">
        <Server class="mt-0.5 h-4 w-4 text-muted-foreground" />
        <div>
          <div class="text-xs text-muted-foreground">Manufacturer</div>
          <div class="text-sm">{{ device.manufacturer || 'Unknown' }}</div>
        </div>
      </div>
      <div class="flex items-start gap-3">
        <Cpu class="mt-0.5 h-4 w-4 text-muted-foreground" />
        <div>
          <div class="text-xs text-muted-foreground">OS</div>
          <div v-if="osGuesses.length > 0" class="space-y-1.5 mt-0.5">
            <div v-for="(guess, i) in visibleGuesses" :key="i" class="flex items-center gap-2">
              <span class="text-sm">{{ guess.name }}</span>
              <span
                v-if="guess.confidence > 0"
                class="inline-flex items-center rounded-full border px-1.5 py-0.5 text-[10px] font-medium leading-none"
                :class="confidenceColor(guess.confidence)"
              >
                {{ guess.confidence }}%
              </span>
            </div>
            <button
              v-if="osGuesses.length > 5"
              class="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
              @click="showAllGuesses = !showAllGuesses"
            >
              <ChevronUp v-if="showAllGuesses" class="h-3 w-3" />
              <ChevronDown v-else class="h-3 w-3" />
              {{ showAllGuesses ? 'Show less' : `Show ${osGuesses.length - 5} more` }}
            </button>
          </div>
          <div v-else class="text-sm">Unknown</div>
        </div>
      </div>
      <div class="flex items-start gap-3">
        <Wifi class="mt-0.5 h-4 w-4 text-muted-foreground" />
        <div>
          <div class="text-xs text-muted-foreground">Device Type</div>
          <div v-if="deviceTypes.length > 0" class="flex flex-wrap gap-1 mt-0.5">
            <span
              v-for="(t, i) in deviceTypes"
              :key="i"
              class="inline-flex items-center rounded-full border border-border bg-muted/50 px-2 py-0.5 text-xs font-medium capitalize"
            >
              {{ t }}
            </span>
          </div>
          <div v-else class="text-sm">Unknown</div>
        </div>
      </div>
      <div class="flex items-start gap-3">
        <Server class="mt-0.5 h-4 w-4 text-muted-foreground" />
        <div>
          <div class="text-xs text-muted-foreground">Added</div>
          <div class="text-sm">{{ formatTimestamp(device.created_at) }}</div>
        </div>
      </div>
    </div>

    <div class="mt-5 border-t border-border pt-4">
      <h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Monitoring Config</h4>
      <div class="grid gap-2 text-sm sm:grid-cols-3">
        <div>
          <span class="text-muted-foreground">Ping Type: </span>
          <span class="font-medium uppercase">{{ device.ping_type }}</span>
        </div>
        <div>
          <span class="text-muted-foreground">Interval: </span>
          <span class="font-medium">{{ device.interval_seconds }}s</span>
        </div>
        <div>
          <span class="text-muted-foreground">Packet Size: </span>
          <span class="font-medium">{{ device.packet_size }} bytes</span>
        </div>
      </div>
    </div>
  </div>
</template>
