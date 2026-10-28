<script setup lang="ts">
// Her parçanın kullanılabilir stoğu kaç gün yetiyor (çubuk) ve yeniden sipariş için kaç gün gerekiyor (dikey çizgi).
// Çubuk çizginin solunda kalıyorsa sipariş gerekir; durum ikon ve yazıyla da gösterilir.
const props = defineProps<{ tedarikciler: RiskliTedarikci[] }>()
const { t, sayi } = useDil()

const satirlar = computed(() => props.tedarikciler.map((t) => {
  const gunluk = t.yillikAdet / 365
  const yeter = t.stok.kullanilabilir / gunluk
  const gerekli = t.stok.siparisSeviyesi / gunluk
  return { t, yeter, gerekli, eksik: yeter < gerekli }
}).sort((a, b) => (a.yeter / a.gerekli) - (b.yeter / b.gerekli)))

const olcek = computed(() => Math.max(1, ...satirlar.value.flatMap(s => [s.yeter, s.gerekli])) * 1.08)
const yuzde = (gun: number) => `${(gun / olcek.value) * 100}%`

const { kapsayici, ipucu, goster, konumla, gizle } = useIpucu()

function ipucuGoster(olay: MouseEvent | FocusEvent, s: (typeof satirlar.value)[number]) {
  goster(olay, `${s.t.parca} · ${s.t.firma}`, [
    { ad: t('grafik.stokYetiyor'), deger: t('genel.gun', { n: Math.round(s.yeter) }), renk: s.eksik ? 'var(--viz-kritik)' : 'var(--viz-iyi)' },
    { ad: t('grafik.siparisIcin'), deger: t('genel.gun', { n: Math.round(s.gerekli) }) },
    { ad: t('grafik.kullanilabilir'), deger: t('genel.adet', { n: sayi(s.t.stok.kullanilabilir) }) },
    { ad: t('grafik.yolSuresi'), deger: t('genel.gun', { n: s.t.rota.transitGun }) }
  ])
}
</script>

<template>
  <div ref="kapsayici" class="relative">
    <ul class="space-y-2.5">
      <li
        v-for="s in satirlar"
        :key="s.t.id"
        tabindex="0"
        class="grid grid-cols-[minmax(0,7rem)_minmax(0,1fr)_minmax(0,8.5rem)] items-center gap-3 rounded-sm outline-none focus-visible:ring-2 focus-visible:ring-primary"
        :aria-label="t('grafik.stokAria', { parca: s.t.parca, a: Math.round(s.yeter), b: Math.round(s.gerekli) }) + (s.eksik ? t('grafik.siparisGerekliAria') : '')"
        @mouseenter="ipucuGoster($event, s)"
        @mousemove="konumla"
        @mouseleave="gizle"
        @focus="ipucuGoster($event, s)"
        @blur="gizle"
      >
        <span class="truncate text-sm text-default">{{ s.t.parca }}</span>
        <span class="relative h-4">
          <span class="absolute inset-y-0 left-0 my-auto h-3 rounded-e-[4px]" :style="{ width: yuzde(s.yeter), background: s.eksik ? 'var(--viz-kritik)' : 'var(--viz-iyi)' }" />
          <span class="absolute inset-y-[-3px] w-0.5 rounded bg-[var(--ui-text-highlighted)]" :style="{ left: yuzde(s.gerekli) }" />
        </span>
        <span class="flex items-center gap-1 text-xs whitespace-nowrap" :class="s.eksik ? 'font-semibold text-highlighted' : 'text-muted'">
          <UIcon :name="s.eksik ? 'i-lucide-triangle-alert' : 'i-lucide-circle-check'" class="size-3.5 shrink-0" :style="{ color: s.eksik ? 'var(--viz-kritik)' : 'var(--viz-iyi)' }" />
          {{ t('grafik.gunOrani', { a: Math.round(s.yeter), b: Math.round(s.gerekli) }) }}
        </span>
      </li>
    </ul>
    <div class="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
      <span class="flex items-center gap-1.5"><span class="inline-block h-2.5 w-4 rounded-sm" style="background: var(--viz-iyi)" /> {{ t('ted.yeterli') }}</span>
      <span class="flex items-center gap-1.5"><span class="inline-block h-2.5 w-4 rounded-sm" style="background: var(--viz-kritik)" /> {{ t('ted.siparisGerekli') }}</span>
      <span class="flex items-center gap-1.5"><span class="inline-block h-3 w-0.5 bg-[var(--ui-text-highlighted)]" /> {{ t('grafik.gerekenGun') }}</span>
    </div>
    <GrafikIpucu v-bind="ipucu" />
  </div>
</template>
