<script setup lang="ts">
import { AlertTriangle, CheckCircle, X, XCircle } from 'lucide-vue-next'
import { formatTimestamp } from '~/lib/utils'

const props = defineProps<{
  notifications: any[]
  unreadCount: number
}>()

const emit = defineEmits<{
  close: []
  markAllRead: []
}>()

function iconForType(type: string) {
  switch (type) {
    case 'device_down': return XCircle
    case 'high_packet_loss': return AlertTriangle
    case 'device_recovered': return CheckCircle
    default: return AlertTriangle
  }
}

function colorForType(type: string) {
  switch (type) {
    case 'device_down': return 'text-red-500'
    case 'high_packet_loss': return 'text-yellow-500'
    case 'device_recovered': return 'text-green-500'
    default: return 'text-muted-foreground'
  }
}
</script>

<template>
  <div class="absolute right-0 top-12 z-50 w-96 rounded-xl border border-border bg-card shadow-2xl shadow-black/20">
    <div class="flex items-center justify-between border-b border-border px-4 py-3">
      <h3 class="text-sm font-semibold">Notifications</h3>
      <div class="flex items-center gap-2">
        <button
          v-if="unreadCount > 0"
          class="text-xs text-primary hover:underline"
          @click="emit('markAllRead')"
        >
          Mark all read
        </button>
        <button class="text-muted-foreground hover:text-foreground" @click="emit('close')">
          <X class="h-4 w-4" />
        </button>
      </div>
    </div>
    <div class="max-h-80 overflow-y-auto">
      <div v-if="notifications.length === 0" class="px-4 py-8 text-center text-sm text-muted-foreground">
        No notifications
      </div>
      <div
        v-for="n in notifications"
        :key="n.id"
        class="flex items-start gap-3 border-b border-border/50 px-4 py-3 last:border-0"
        :class="{ 'opacity-50': n.is_read }"
      >
        <component :is="iconForType(n.type)" class="mt-0.5 h-4 w-4 shrink-0" :class="colorForType(n.type)" />
        <div class="min-w-0 flex-1">
          <p class="text-sm">{{ n.message }}</p>
          <p class="mt-0.5 text-xs text-muted-foreground">{{ formatTimestamp(n.created_at) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
