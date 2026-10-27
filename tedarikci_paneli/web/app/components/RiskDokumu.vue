<script setup lang="ts">
defineProps<{ risk: RiskSonucu }>()
</script>

<template>
  <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
    <div v-for="b in risk.bilesenler" :key="b.ad" class="space-y-1.5">
      <div class="flex items-baseline justify-between text-sm">
        <span class="font-medium text-highlighted">{{ b.ad }}</span>
        <span class="tabular-nums text-muted">{{ sayiBicimi(b.puan) }} / {{ b.enFazla }}</span>
      </div>
      <UProgress :model-value="b.puan" :max="b.enFazla" size="sm" :color="b.puan / b.enFazla >= 0.6 ? 'error' : 'primary'" />
      <p class="text-xs text-muted whitespace-normal">{{ b.aciklama }}</p>
    </div>
  </div>
</template>
