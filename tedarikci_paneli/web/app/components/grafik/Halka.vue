<script setup lang="ts">
// Parça-bütün halkası (en fazla 6 dilim). Dilimler arasında 2px zemin boşluğu; değerler lejantta da yazılı.
import type { Dilim } from '~/utils/grafik'

const props = defineProps<{ dilimler: Dilim[], ortaDeger: string, ortaEtiket: string }>()

const R = 70
const KALINLIK = 22
const toplam = computed(() => props.dilimler.reduce((t, d) => t + d.deger, 0))

const yaylar = computed(() => {
  let bas = 0
  const BOSLUK = toplam.value && props.dilimler.filter(d => d.deger).length > 1 ? 0.012 : 0
  return props.dilimler.filter(d => d.deger > 0).map((d) => {
    const oran = d.deger / toplam.value
    const a1 = bas + BOSLUK / 2
    const a2 = bas + oran - BOSLUK / 2
    bas += oran
    // Yuvarlama: sunucu ve tarayıcı trigonometriyi son basamakta farklı hesaplayabilir (hydration uyarısı)
    const yuvarla = (v: number) => Math.round(v * 100) / 100
    const xy = (o: number) => [yuvarla(100 + R * Math.sin(o * 2 * Math.PI)), yuvarla(100 - R * Math.cos(o * 2 * Math.PI))]
    const [x1, y1] = xy(a1)
    const [x2, y2] = xy(a2)
    const buyuk = a2 - a1 > 0.5 ? 1 : 0
    const d0 = oran >= 0.999
      ? `M 100 ${100 - R} A ${R} ${R} 0 1 1 99.99 ${100 - R}`
      : `M ${x1} ${y1} A ${R} ${R} 0 ${buyuk} 1 ${x2} ${y2}`
    return { ...d, d: d0, oran }
  })
})

const { kapsayici, ipucu, goster, konumla, gizle } = useIpucu()
const aktif = ref<string | null>(null)

function ipucuGoster(olay: MouseEvent | FocusEvent, d: Dilim & { oran: number }) {
  aktif.value = d.ad
  goster(olay, d.ad, [
    { ad: 'Sayı', deger: sayiBicimi(d.deger), renk: d.renk },
    { ad: 'Pay', deger: `%${Math.round(d.oran * 100)}` }
  ])
}
function birak() {
  aktif.value = null
  gizle()
}
</script>

<template>
  <div ref="kapsayici" class="relative flex flex-wrap items-center gap-5">
    <svg viewBox="0 0 200 200" class="w-36 shrink-0" role="img" :aria-label="dilimler.map(d => `${d.ad} ${d.deger}`).join(', ')">
      <circle cx="100" cy="100" :r="R" fill="none" stroke="var(--viz-cizgi)" :stroke-width="KALINLIK" />
      <path
        v-for="y in yaylar"
        :key="y.ad"
        :d="y.d"
        fill="none"
        :stroke="y.renk"
        :stroke-width="aktif === y.ad ? KALINLIK + 4 : KALINLIK"
        tabindex="0"
        class="cursor-pointer outline-none transition-[stroke-width]"
        @mouseenter="ipucuGoster($event, y)"
        @mousemove="konumla"
        @mouseleave="birak"
        @focus="ipucuGoster($event, y)"
        @blur="birak"
      />
      <text x="100" y="98" text-anchor="middle" class="text-[34px] font-semibold" fill="var(--ui-text-highlighted)">{{ ortaDeger }}</text>
      <text x="100" y="122" text-anchor="middle" class="text-[13px]" fill="var(--ui-text-muted)">{{ ortaEtiket }}</text>
    </svg>

    <ul class="space-y-2 text-sm min-w-0">
      <li v-for="d in dilimler" :key="d.ad" class="flex items-center gap-2">
        <span class="inline-block size-3 rounded-sm shrink-0" :style="{ background: d.renk }" />
        <UIcon v-if="d.ikon" :name="d.ikon" class="size-4 shrink-0 text-muted" />
        <span class="text-default">{{ d.ad }}</span>
        <span class="ms-auto ps-3 font-semibold text-highlighted tabular-nums">{{ sayiBicimi(d.deger) }}</span>
      </li>
    </ul>

    <GrafikIpucu v-bind="ipucu" />
  </div>
</template>
