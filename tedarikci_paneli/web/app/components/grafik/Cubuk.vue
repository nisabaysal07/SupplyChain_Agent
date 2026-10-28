<script setup lang="ts">
// Yatay çubuk grafiği, tek seri (tek renk). Değer çubuğun ucunda yazılı; ayrıntı ipucunda.
import type { Cubuk } from '~/utils/grafik'

const props = withDefaults(
  defineProps<{ cubuklar: Cubuk[], renk?: string, etiketGenisligi?: string }>(),
  { renk: 'var(--viz-1)', etiketGenisligi: '7rem' }
)

const enBuyuk = computed(() => Math.max(1, ...props.cubuklar.map(c => c.deger)))
const { kapsayici, ipucu, goster, konumla, gizle } = useIpucu()
const aktif = ref<string | null>(null)
const { t } = useDil()

function ipucuGoster(olay: MouseEvent | FocusEvent, c: Cubuk) {
  aktif.value = c.ad
  goster(olay, c.ad, [{ ad: t('alan.deger'), deger: c.etiket, renk: props.renk }, ...(c.ayrinti ?? [])])
}
function birak() {
  aktif.value = null
  gizle()
}
</script>

<template>
  <div ref="kapsayici" class="relative">
    <ul class="space-y-2.5">
      <li
        v-for="c in cubuklar"
        :key="c.ad"
        tabindex="0"
        class="grid items-center gap-3 rounded-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
        :style="{ gridTemplateColumns: `minmax(0, ${etiketGenisligi}) minmax(0, 1fr)` }"
        :aria-label="`${c.ad}: ${c.etiket}`"
        @mouseenter="ipucuGoster($event, c)"
        @mousemove="konumla"
        @mouseleave="birak"
        @focus="ipucuGoster($event, c)"
        @blur="birak"
      >
        <span class="line-clamp-2 text-sm leading-snug text-default" :title="c.ad">{{ c.ad }}</span>
        <span class="flex items-center gap-2 min-w-0">
          <span
            class="h-3.5 rounded-e-[4px] transition-opacity"
            :style="{ width: `max(2px, ${(c.deger / enBuyuk) * 80}%)`, background: renk, opacity: aktif && aktif !== c.ad ? 0.45 : 1 }"
          />
          <span class="text-xs font-medium text-toned tabular-nums whitespace-nowrap">{{ c.etiket }}</span>
        </span>
      </li>
    </ul>
    <GrafikIpucu v-bind="ipucu" />
  </div>
</template>
