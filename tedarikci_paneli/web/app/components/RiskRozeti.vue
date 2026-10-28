<script setup lang="ts">
defineProps<{ risk: RiskSonucu }>()
const { t } = useDil()
</script>

<template>
  <SeviyeRozeti :seviye="risk.seviye">
    {{ risk.skor }} · {{ t(`seviye.${risk.seviye}`) }}
  </SeviyeRozeti>
</template>
