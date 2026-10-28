<script setup lang="ts">
// 0–100 risk göstergesi: yarım daire, eşikler (35 ve 60) işaretli, ortada büyük sayı
const props = defineProps<{ skor: number }>()
const { t } = useDil()

const R = 80
const CX = 100
const CY = 96
// Sunucu ve tarayıcı trigonometriyi son basamakta farklı hesaplayabilir; yuvarlanmazsa hydration uyarısı verir
const yuvarla = (v: number) => Math.round(v * 100) / 100
const nokta = (oran: number, r = R) => {
  const aci = Math.PI * (1 - oran)
  return [yuvarla(CX + r * Math.cos(aci)), yuvarla(CY - r * Math.sin(aci))] as const
}
const yay = (bas: number, son: number) => {
  const [x1, y1] = nokta(bas)
  const [x2, y2] = nokta(son)
  return `M ${x1} ${y1} A ${R} ${R} 0 0 1 ${x2} ${y2}`
}

const seviye = computed(() => seviyeBul(props.skor))
const oran = computed(() => Math.min(1, Math.max(0, props.skor / 100)))
const SEVIYE_IKONU: Record<Seviye, string> = {
  dusuk: 'i-lucide-circle-check', orta: 'i-lucide-circle-alert', yuksek: 'i-lucide-triangle-alert'
}
const esikler = [35, 60].map((e) => {
  const [x1, y1] = nokta(e / 100, R - 11)
  const [x2, y2] = nokta(e / 100, R + 11)
  return { e, x1, y1, x2, y2 }
})
</script>

<template>
  <div class="flex flex-col items-center">
    <svg viewBox="0 0 200 112" class="w-full max-w-60" role="img" :aria-label="t('grafik.portfoyAria', { skor, s: t(`seviye.${seviye}`) })">
      <path :d="yay(0, 1)" fill="none" stroke="var(--viz-cizgi)" stroke-width="14" stroke-linecap="round" />
      <path v-if="oran > 0" :d="yay(0, oran)" fill="none" :stroke="SEVIYE_VIZ_RENGI[seviye]" stroke-width="14" stroke-linecap="round" />
      <line
        v-for="e in esikler"
        :key="e.e"
        :x1="e.x1"
        :y1="e.y1"
        :x2="e.x2"
        :y2="e.y2"
        stroke="var(--ui-text-muted)"
        stroke-width="1.5"
      />
      <text x="22" y="110" text-anchor="middle" class="text-[10px]" fill="var(--ui-text-muted)">0</text>
      <text x="178" y="110" text-anchor="middle" class="text-[10px]" fill="var(--ui-text-muted)">100</text>
    </svg>
    <p class="-mt-12 text-4xl font-semibold text-highlighted">{{ skor }}</p>
    <p class="mt-1 flex items-center gap-1 text-sm font-medium text-toned">
      <UIcon :name="SEVIYE_IKONU[seviye]" class="size-4" :style="{ color: SEVIYE_VIZ_RENGI[seviye] }" />
      {{ t(`seviyeRisk.${seviye}`) }}
    </p>
    <p class="mt-1 text-xs text-muted">{{ t('grafik.esikler') }}</p>
  </div>
</template>
