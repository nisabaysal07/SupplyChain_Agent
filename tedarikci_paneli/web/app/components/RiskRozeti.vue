<script setup lang="ts">
defineProps<{ risk: RiskSonucu }>()
</script>

<template>
  <SeviyeRozeti :seviye="risk.seviye">
    {{ risk.skor }} · {{ SEVIYE_ETIKETI[risk.seviye] }}
  </SeviyeRozeti>
</template>
