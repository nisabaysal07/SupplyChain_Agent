<script setup lang="ts">
defineProps<{ olay: EtkiliOlay, secili: boolean }>()
defineEmits<{ sec: [] }>()
</script>

<template>
  <button
    type="button"
    class="w-full text-left rounded-lg border border-default seviye-serit p-3 transition-colors hover:bg-elevated/60"
    :class="[`seviye-serit--${olay.siddet}`, secili ? 'bg-elevated ring-1 ring-primary' : 'bg-default']"
    :aria-current="secili ? 'true' : undefined"
    @click="$emit('sec')"
  >
    <div class="flex items-start justify-between gap-2">
      <p class="font-medium text-highlighted line-clamp-2">{{ olay.baslik }}</p>
      <SeviyeRozeti :seviye="olay.siddet" class="shrink-0" />
    </div>
    <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
      <span class="flex items-center gap-1">
        <UIcon :name="OLAY_TURU[olay.tur].icon" class="size-3.5" />
        {{ OLAY_TURU[olay.tur].etiket }}
      </span>
      <span>{{ tarihBicimi(olay.tarih) }}</span>
      <span>{{ olay.etkilenenler.length }} tedarikçi</span>
      <span v-if="olay.gecikmeVar" class="flex items-center gap-1 font-medium text-toned">
        <UIcon name="i-lucide-clock-alert" class="size-3.5" />
        Gecikme
      </span>
      <span v-if="olay.analizVar" class="flex items-center gap-1 font-medium text-primary">
        <UIcon name="i-lucide-bot" class="size-3.5" />
        Model çıkarımı
      </span>
    </div>
  </button>
</template>
