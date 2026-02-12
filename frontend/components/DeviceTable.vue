<script setup lang="ts">
import { Eye, MoreHorizontal, Pause, Play, Trash2 } from 'lucide-vue-next'
import { formatLatency, lossColor } from '~/lib/utils'

const props = defineProps<{
  devices: any[]
  loading: boolean
}>()

const emit = defineEmits<{
  toggle: [id: number]
  delete: [id: number]
}>()

const showMenu = ref<number | null>(null)

function toggleMenu(id: number) {
  showMenu.value = showMenu.value === id ? null : id
}

function fmtLoss(v: number | null | undefined): string {
  if (v === null || v === undefined) return '-'
  return v.toFixed(2) + '%'
}
</script>

<template>
  <div class="rounded-xl border border-border bg-card overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-border bg-muted/50">
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">Device</th>
            <th class="px-4 py-3 text-left font-medium text-muted-foreground">IP / MAC</th>
            <th class="px-4 py-3 text-center font-medium text-muted-foreground">Status</th>
            <th class="px-4 py-3 text-center font-medium text-muted-foreground">Type</th>
            <th class="px-4 py-3 text-right font-medium text-muted-foreground">6h</th>
            <th class="px-4 py-3 text-right font-medium text-muted-foreground">12h</th>
            <th class="px-4 py-3 text-right font-medium text-muted-foreground">24h</th>
            <th class="px-4 py-3 text-right font-medium text-muted-foreground">48h</th>
            <th class="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && devices.length === 0">
            <td colspan="9" class="px-4 py-12 text-center text-muted-foreground">
              <div class="flex items-center justify-center gap-2">
                <div class="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                Loading devices...
              </div>
            </td>
          </tr>
          <tr v-else-if="devices.length === 0">
            <td colspan="9" class="px-4 py-12 text-center text-muted-foreground">
              No devices yet. Add a device or scan your network to get started.
            </td>
          </tr>
          <tr
            v-for="device in devices"
            :key="device.id"
            class="border-b border-border/50 last:border-0 hover:bg-muted/30 transition-colors"
          >
            <td class="px-4 py-3">
              <NuxtLink :to="`/device/${device.id}`" class="font-medium hover:text-primary transition-colors">
                {{ device.name }}
              </NuxtLink>
              <div v-if="device.manufacturer" class="text-xs text-muted-foreground">{{ device.manufacturer }}</div>
            </td>
            <td class="px-4 py-3">
              <div class="font-mono text-xs">{{ device.ip_address || '-' }}</div>
              <div v-if="device.mac_address" class="font-mono text-xs text-muted-foreground">{{ device.mac_address }}</div>
            </td>
            <td class="px-4 py-3 text-center">
              <StatusBadge :status="device.monitoring_enabled ? device.status : 'unknown'" />
            </td>
            <td class="px-4 py-3 text-center">
              <span class="rounded-md bg-muted px-2 py-0.5 text-xs font-medium uppercase">{{ device.ping_type }}</span>
            </td>
            <td class="px-4 py-3 text-right font-mono text-xs" :class="lossColor(device.stats_6h)">{{ fmtLoss(device.stats_6h) }}</td>
            <td class="px-4 py-3 text-right font-mono text-xs" :class="lossColor(device.stats_12h)">{{ fmtLoss(device.stats_12h) }}</td>
            <td class="px-4 py-3 text-right font-mono text-xs" :class="lossColor(device.stats_24h)">{{ fmtLoss(device.stats_24h) }}</td>
            <td class="px-4 py-3 text-right font-mono text-xs" :class="lossColor(device.stats_48h)">{{ fmtLoss(device.stats_48h) }}</td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-1">
                <NuxtLink
                  :to="`/device/${device.id}`"
                  class="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-accent transition-colors"
                  title="View details"
                >
                  <Eye class="h-4 w-4 text-muted-foreground" />
                </NuxtLink>
                <button
                  class="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-accent transition-colors"
                  :title="device.monitoring_enabled ? 'Pause monitoring' : 'Resume monitoring'"
                  @click="emit('toggle', device.id)"
                >
                  <Pause v-if="device.monitoring_enabled" class="h-4 w-4 text-muted-foreground" />
                  <Play v-else class="h-4 w-4 text-muted-foreground" />
                </button>
                <div class="relative">
                  <button
                    class="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-accent transition-colors"
                    @click="toggleMenu(device.id)"
                  >
                    <MoreHorizontal class="h-4 w-4 text-muted-foreground" />
                  </button>
                  <div
                    v-if="showMenu === device.id"
                    class="absolute right-0 top-9 z-10 w-40 rounded-lg border border-border bg-card py-1 shadow-lg"
                  >
                    <button
                      class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-500 hover:bg-muted"
                      @click="emit('delete', device.id); showMenu = null"
                    >
                      <Trash2 class="h-3.5 w-3.5" />
                      Delete device
                    </button>
                  </div>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
