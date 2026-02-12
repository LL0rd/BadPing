<script setup lang="ts">
import { Moon, Sun } from 'lucide-vue-next'

const colorMode = useColorMode()

function toggle() {
  colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
}
</script>

<template>
  <button
    class="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card hover:bg-accent transition-colors"
    @click="toggle"
  >
    <Sun v-if="colorMode.value === 'dark'" class="h-4 w-4" />
    <Moon v-else class="h-4 w-4" />
  </button>
</template>
