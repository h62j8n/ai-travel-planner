<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { checkHealth } from '@/api/health'

const status = ref<'checking' | 'ok' | 'error'>('checking')

onMounted(async () => {
  try {
    await checkHealth()
    status.value = 'ok'
  } catch {
    status.value = 'error'
  }
})
</script>

<template>
  <section>
    <p>Backend status: {{ status }}</p>
  </section>
</template>
