<script setup lang="ts">
// Düşük / Orta / Yüksek rozeti. Renk her zaman yazıyla birlikte; stil: app/assets/css/main.css (.seviye-rozeti)
withDefaults(defineProps<{ seviye: Seviye, buyuk?: boolean }>(), { buyuk: false })
</script>

<template>
  <span class="seviye-rozeti tabular-nums" :class="[`seviye-rozeti--${seviye}`, { 'seviye-rozeti--buyuk': buyuk }]">
    <span class="seviye-rozeti__lamba" aria-hidden="true" />
    <slot>{{ SEVIYE_ETIKETI[seviye] }}</slot>
  </span>
</template>
