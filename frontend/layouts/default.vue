<script setup lang="ts">
import { Activity, AlertTriangle, Bell, BellDot } from 'lucide-vue-next'

const { unreadCount, notifications, fetchNotifications, markAllRead, startPolling, stopPolling } = useNotifications()
const showNotifications = ref(false)
const arpAvailable = ref(true)
const api = useApi()

provide('arpAvailable', arpAvailable)

onMounted(async () => {
  startPolling()
  try {
    const status = await api.get<{ arp_available: boolean }>('/status')
    arpAvailable.value = status.arp_available
  } catch {}
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="min-h-screen bg-background">
    <header class="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm">
      <div class="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        <NuxtLink to="/" class="flex items-center gap-3 hover:opacity-80 transition-opacity">
          <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
            <Activity class="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 class="text-lg font-bold leading-none">BadPing</h1>
            <p class="text-xs text-muted-foreground">Network Monitor</p>
          </div>
        </NuxtLink>

        <div class="flex items-center gap-3">
          <ThemeToggle />

          <div class="relative">
            <button
              class="relative flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card hover:bg-accent transition-colors"
              @click="showNotifications = !showNotifications"
            >
              <BellDot v-if="unreadCount > 0" class="h-4 w-4 text-primary" />
              <Bell v-else class="h-4 w-4 text-muted-foreground" />
              <span
                v-if="unreadCount > 0"
                class="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-primary-foreground"
              >
                {{ unreadCount > 99 ? '99+' : unreadCount }}
              </span>
            </button>

            <NotificationBanner
              v-if="showNotifications"
              :notifications="notifications"
              :unread-count="unreadCount"
              @close="showNotifications = false"
              @mark-all-read="markAllRead"
            />
          </div>
        </div>
      </div>
    </header>

    <div
      v-if="!arpAvailable"
      class="border-b border-yellow-500/20 bg-yellow-500/10"
    >
      <div class="mx-auto flex max-w-7xl items-center gap-3 px-4 py-2.5 sm:px-6">
        <AlertTriangle class="h-4 w-4 shrink-0 text-yellow-500" />
        <p class="text-sm text-yellow-200">
          <span class="font-medium">ARP features unavailable</span> — Running without root privileges. ARP ping and network discovery are disabled. Run in Docker with <code class="rounded bg-yellow-500/20 px-1 py-0.5 text-xs">NET_RAW</code> / <code class="rounded bg-yellow-500/20 px-1 py-0.5 text-xs">NET_ADMIN</code> capabilities to enable them.
        </p>
      </div>
    </div>

    <main class="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <slot />
    </main>
  </div>
</template>
