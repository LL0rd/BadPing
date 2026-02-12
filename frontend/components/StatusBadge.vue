<script setup lang="ts">
import { statusBg } from '~/lib/utils'

const props = defineProps<{
  status: string
}>()
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize"
    :class="statusBg(status)"
  >
    <span class="h-1.5 w-1.5 rounded-full" :class="{
      'bg-green-500': status === 'online',
      'bg-red-500': status === 'offline',
      'bg-yellow-500': status === 'degraded',
      'bg-muted-foreground': status === 'unknown',
    }" />
    {{ status }}
  </span>
</template>
