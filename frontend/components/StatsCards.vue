<script setup lang="ts">
import { Activity, AlertTriangle, Clock, Gauge } from 'lucide-vue-next'

const props = defineProps<{
  stats: {
    device_id: number
    stats_6h: number
    stats_12h: number
    stats_24h: number
    stats_48h: number
    total_pings_24h: number
    lost_pings_24h: number
    ok_pings_24h: number
    avg_latency_24h: number | null
    min_latency_24h: number | null
    max_latency_24h: number | null
  } | null
}>()

function fmtLoss(v: number): string {
  return v.toFixed(2) + '%'
}

function fmtLatency(v: number | null): string {
  if (v === null) return '-'
  return v.toFixed(1) + 'ms'
}
</script>

<template>
  <div v-if="stats" class="grid grid-cols-2 gap-3 lg:grid-cols-4">
    <div class="rounded-xl border border-border bg-card p-4">
      <div class="mb-2 flex items-center gap-2 text-muted-foreground">
        <Activity class="h-4 w-4" />
        <span class="text-xs font-medium uppercase tracking-wider">Packet Loss</span>
      </div>
      <div class="space-y-1.5 text-sm">
        <div class="flex justify-between">
          <span class="text-muted-foreground">6h</span>
          <span class="font-mono font-medium" :class="stats.stats_6h === 0 ? 'text-green-500' : stats.stats_6h < 5 ? 'text-yellow-500' : 'text-red-500'">{{ fmtLoss(stats.stats_6h) }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-muted-foreground">12h</span>
          <span class="font-mono font-medium" :class="stats.stats_12h === 0 ? 'text-green-500' : stats.stats_12h < 5 ? 'text-yellow-500' : 'text-red-500'">{{ fmtLoss(stats.stats_12h) }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-muted-foreground">24h</span>
          <span class="font-mono font-medium" :class="stats.stats_24h === 0 ? 'text-green-500' : stats.stats_24h < 5 ? 'text-yellow-500' : 'text-red-500'">{{ fmtLoss(stats.stats_24h) }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-muted-foreground">48h</span>
          <span class="font-mono font-medium" :class="stats.stats_48h === 0 ? 'text-green-500' : stats.stats_48h < 5 ? 'text-yellow-500' : 'text-red-500'">{{ fmtLoss(stats.stats_48h) }}</span>
        </div>
      </div>
    </div>

    <div class="rounded-xl border border-border bg-card p-4">
      <div class="mb-2 flex items-center gap-2 text-muted-foreground">
        <Gauge class="h-4 w-4" />
        <span class="text-xs font-medium uppercase tracking-wider">Latency (24h)</span>
      </div>
      <div class="space-y-1.5 text-sm">
        <div class="flex justify-between">
          <span class="text-muted-foreground">Avg</span>
          <span class="font-mono font-medium">{{ fmtLatency(stats.avg_latency_24h) }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-muted-foreground">Min</span>
          <span class="font-mono font-medium text-green-500">{{ fmtLatency(stats.min_latency_24h) }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-muted-foreground">Max</span>
          <span class="font-mono font-medium text-red-500">{{ fmtLatency(stats.max_latency_24h) }}</span>
        </div>
      </div>
    </div>

    <div class="rounded-xl border border-border bg-card p-4">
      <div class="mb-2 flex items-center gap-2 text-muted-foreground">
        <Clock class="h-4 w-4" />
        <span class="text-xs font-medium uppercase tracking-wider">Pings (24h)</span>
      </div>
      <div class="mt-3">
        <div class="text-2xl font-bold">{{ stats.total_pings_24h.toLocaleString() }}</div>
        <div class="text-xs text-muted-foreground">total pings sent</div>
      </div>
    </div>

    <div class="rounded-xl border border-border bg-card p-4">
      <div class="mb-2 flex items-center gap-2 text-muted-foreground">
        <AlertTriangle class="h-4 w-4" />
        <span class="text-xs font-medium uppercase tracking-wider">Results (24h)</span>
      </div>
      <div class="mt-1 space-y-1 text-sm">
        <div class="flex justify-between">
          <span class="text-muted-foreground">OK</span>
          <span class="font-mono font-medium text-green-500">{{ stats.ok_pings_24h.toLocaleString() }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-muted-foreground">Lost</span>
          <span class="font-mono font-medium" :class="stats.lost_pings_24h === 0 ? 'text-green-500' : 'text-red-500'">{{ stats.lost_pings_24h.toLocaleString() }}</span>
        </div>
      </div>
    </div>
  </div>

  <div v-else class="grid grid-cols-2 gap-3 lg:grid-cols-4">
    <div v-for="i in 4" :key="i" class="h-32 animate-pulse rounded-xl border border-border bg-card" />
  </div>
</template>
