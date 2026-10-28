<script setup lang="ts">
// Düşük / Orta / Yüksek rozeti. Renk her zaman yazıyla birlikte; stil: app/assets/css/main.css (.seviye-rozeti)
withDefaults(defineProps<{ seviye: Seviye, buyuk?: boolean }>(), { buyuk: false })
const { t } = useDil()
</script>

<template>
  <span class="seviye-rozeti tabular-nums" :class="[`seviye-rozeti--${seviye}`, { 'seviye-rozeti--buyuk': buyuk }]">
    <span class="seviye-rozeti__lamba" aria-hidden="true" />
    <slot>{{ t(`seviye.${seviye}`) }}</slot>
  </span>
</template>
