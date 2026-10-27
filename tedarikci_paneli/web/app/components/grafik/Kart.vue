<script setup lang="ts">
// Her grafiğin tablo görünümü vardır: değerler yalnızca renge veya ipucuna bağlı kalmaz
import type { GrafikTablosu } from '~/utils/grafik'

defineProps<{ baslik: string, aciklama?: string, tablo: GrafikTablosu }>()
const tabloAcik = ref(false)
</script>

<template>
  <UCard :ui="{ body: 'p-4 sm:p-5' }" class="min-w-0">
    <div class="flex items-start justify-between gap-3 mb-3">
      <div class="min-w-0">
        <h2 class="font-semibold text-highlighted">{{ baslik }}</h2>
        <p v-if="aciklama" class="text-sm text-muted">{{ aciklama }}</p>
      </div>
      <div class="flex items-center gap-1 shrink-0">
        <slot name="sag" />
        <UButton
          size="xs"
          color="neutral"
          variant="ghost"
          :icon="tabloAcik ? 'i-lucide-chart-column' : 'i-lucide-table'"
          :label="tabloAcik ? 'Grafik' : 'Tablo'"
          :aria-pressed="tabloAcik"
          @click="tabloAcik = !tabloAcik"
        />
      </div>
    </div>

    <div v-if="tabloAcik" class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-default text-left text-muted">
            <th v-for="(b, i) in tablo.basliklar" :key="b" class="py-1.5 pr-3 font-medium" :class="i ? 'text-right' : ''">{{ b }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(s, j) in tablo.satirlar" :key="j" class="border-b border-default last:border-0">
            <td v-for="(h, i) in s" :key="i" class="py-1.5 pr-3 text-default" :class="i ? 'text-right tabular-nums' : ''">{{ h }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <slot v-else />
  </UCard>
</template>
