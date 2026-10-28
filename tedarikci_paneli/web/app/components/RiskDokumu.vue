<script setup lang="ts">
defineProps<{ risk: RiskSonucu }>()
const { t, ondalik, yuzde, ulkeAdi } = useDil()

// Sunucu her bileşen için kod ve değerleri gönderir; açıklama seçili dilde burada yazılır
function aciklama(b: RiskBileseni): string {
  const d = b.degerler
  const n = Number(d.sayi ?? d.kalan ?? 0)
  switch (b.kod) {
    case 'stok': return t('risk.stok', { oran: yuzde(Number(d.oran)), gun: Number(d.gun) })
    case 'rota': return t('risk.rota', { mod: t(d.mod === 'hava' ? 'risk.hava' : 'risk.deniz'), gun: t('genel.gun', { n: Number(d.gun) }) })
    case 'ticaret': return `${ulkeAdi(String(d.ulke))}: ${t(d.anlasma ? 'risk.anlasmaVar' : 'risk.anlasmaYok')}, ${
      Number(d.vergi) > 0 ? t('risk.vergiVar', { v: yuzde(Number(d.vergi)) }) : t('risk.vergiYok')}`
    case 'sozlesme': return n < 0 ? t('risk.sozlesmeBitti', { n: -n }) : t('risk.sozlesmeKalan', { n })
    case 'olaylar': return n ? t('risk.olayVar', { n, baslik: String(d.enAgir) }) : t('risk.olayYok')
    default: return b.aciklama
  }
}
</script>

<template>
  <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
    <div v-for="b in risk.bilesenler" :key="b.kod" class="space-y-1.5">
      <div class="flex items-baseline justify-between text-sm">
        <span class="font-medium text-highlighted">{{ t(`risk.ad.${b.kod}`) }}</span>
        <span class="tabular-nums text-muted">{{ ondalik(b.puan) }} / {{ b.enFazla }}</span>
      </div>
      <UProgress :model-value="b.puan" :max="b.enFazla" size="sm" :color="b.puan / b.enFazla >= 0.6 ? 'error' : 'primary'" />
      <p class="text-xs text-muted whitespace-normal">{{ aciklama(b) }}</p>
    </div>
  </div>
</template>
