<script setup lang="ts">
// Bütün görseller /api/tedarikciler ve /api/olaylar verisinden türetilir; ek veritabanı sorgusu gerekmez
const [{ data: tedarikciler }, { data: olaylar }] = await Promise.all([
  useFetch<RiskliTedarikci[]>('/api/tedarikciler', { default: () => [] }),
  useFetch<EtkiliOlay[]>('/api/olaylar', { default: () => [] })
])

const { t, para, sayi, yuzde, ulkeAdi } = useDil()
const portfoy = computed(() => portfoySkoru(tedarikciler.value))
const SEVIYELER = ['yuksek', 'orta', 'dusuk'] as const
const SEVIYE_IKONU: Record<Seviye, string> = {
  dusuk: 'i-lucide-circle-check', orta: 'i-lucide-circle-alert', yuksek: 'i-lucide-triangle-alert'
}

const ozet = computed(() => {
  const liste = tedarikciler.value
  return [
    {
      baslik: t('pano.yuksekRiskli'),
      deger: sayi(liste.filter(x => x.risk.seviye === 'yuksek').length),
      alt: t('pano.tedarikcidenN', { n: sayi(liste.length) }),
      icon: 'i-lucide-shield-alert',
      to: { path: '/tedarikciler', query: { risk: 'yuksek' } }
    },
    {
      baslik: t('pano.aktifOlay'),
      deger: sayi(olaylar.value.length),
      alt: t('pano.olayAlt', { yuksek: olaylar.value.filter(o => o.siddet === 'yuksek').length, gecikme: olaylar.value.filter(o => o.gecikmeVar).length }),
      icon: 'i-lucide-circle-alert',
      to: { path: '/olaylar' }
    },
    {
      baslik: t('pano.ekMaliyet'),
      deger: para(olaylar.value.reduce((top, o) => top + o.toplamMaliyetEtkisiUsd, 0)),
      alt: t('pano.ekMaliyetAlt', { oran: yuzde(olaylar.value.reduce((top, o) => top + o.toplamMaliyetEtkisiUsd, 0) / Math.max(1, liste.reduce((top, x) => top + x.yillikAlimUsd, 0))) }),
      icon: 'i-lucide-wallet',
      // Olaylar sayfası "olaylara göre yıllık ek maliyet" grafiğiyle açılır
      to: { path: '/olaylar' }
    },
    {
      baslik: t('pano.siparisGereken'),
      deger: sayi(liste.filter(x => x.stok.durum === 'siparis_gerekli').length),
      alt: t('pano.siparisAlt'),
      icon: 'i-lucide-package-open',
      to: { path: '/tedarikciler', query: { stok: 'siparis_gerekli', sirala: 'stok' } }
    }
  ]
})

// Risk dağılımı (halka)
const dagilim = computed(() => SEVIYELER.map(s => ({
  ad: t(`seviye.${s}`),
  deger: tedarikciler.value.filter(x => x.risk.seviye === s).length,
  renk: SEVIYE_VIZ_RENGI[s],
  ikon: SEVIYE_IKONU[s]
})))

// Menşe ülkeye göre yıllık alım (çubuk)
const ulkeler = computed(() => {
  const gruplar = new Map<string, RiskliTedarikci[]>()
  for (const x of tedarikciler.value) gruplar.set(x.menseUlke, [...(gruplar.get(x.menseUlke) ?? []), x])
  return [...gruplar.entries()]
    .map(([ulke, liste]) => {
      const alim = liste.reduce((top, x) => top + x.yillikAlimUsd, 0)
      return {
        ad: ulkeAdi(ulke),
        deger: alim,
        etiket: para(alim),
        ayrinti: [
          { ad: t('alan.tedarikci'), deger: liste.map(x => x.firma).join(', ') },
          { ad: t('alan.ortalamaRisk'), deger: sayi(Math.round(portfoySkoru(liste))) }
        ]
      }
    })
    .sort((a, b) => b.deger - a.deger)
})

// En kritik olaylar: önce şiddet, sonra tarih
const SIRA: Record<Seviye, number> = { yuksek: 0, orta: 1, dusuk: 2 }
const kritikOlaylar = computed(() => [...olaylar.value]
  .sort((a, b) => SIRA[a.siddet] - SIRA[b.siddet] || b.tarih.localeCompare(a.tarih))
  .slice(0, 4))

// Tablo görünümleri
const dagilimTablosu = computed(() => ({
  basliklar: [t('alan.seviye'), t('alan.tedarikci')],
  satirlar: dagilim.value.map(d => [d.ad, String(d.deger)])
}))
const haritaTablosu = computed(() => ({
  basliklar: [t('alan.tedarikci'), t('alan.cikis'), t('alan.varis'), t('alan.yillikAlim'), t('alan.risk')],
  satirlar: [...tedarikciler.value].sort((a, b) => b.risk.skor - a.risk.skor).map(x => [
    `${x.firma} · ${x.parca}`, x.rota.cikis, x.rota.varis, para(x.yillikAlimUsd), `${x.risk.skor} · ${t(`seviye.${x.risk.seviye}`)}`
  ])
}))
const ulkeTablosu = computed(() => ({
  basliklar: [t('alan.menseUlke'), t('alan.yillikAlim')],
  satirlar: ulkeler.value.map(u => [u.ad, u.etiket])
}))
</script>

<template>
  <SayfaPaneli :baslik="t('nav.pano')">
    <div class="space-y-6">
      <!-- Özet kutucukları: her biri ilgili listeye (filtreli) götürür -->
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <NuxtLink
          v-for="k in ozet"
          :key="k.baslik"
          :to="k.to"
          class="group block rounded-lg basilabilir outline-primary/25 focus-visible:outline-3"
        >
          <UCard :ui="{ body: 'p-4 sm:p-5' }" class="h-full transition-colors group-hover:bg-elevated/60">
            <div class="flex items-center gap-2">
              <UIcon :name="k.icon" class="size-5 text-primary" />
              <p class="text-sm font-medium text-muted">{{ k.baslik }}</p>
              <UIcon name="i-lucide-arrow-up-right" class="ms-auto size-4 text-dimmed transition-colors group-hover:text-primary" />
            </div>
            <p class="mt-2 text-3xl font-semibold text-highlighted">{{ k.deger }}</p>
            <p class="text-sm text-muted">{{ k.alt }}</p>
          </UCard>
        </NuxtLink>
      </div>

      <!-- En kritik olaylar: özet kutucuklarının hemen altında, yatay -->
      <UCard :ui="{ body: 'p-4 sm:p-5' }">
        <div class="flex items-center justify-between mb-3">
          <h2 class="font-semibold text-highlighted">{{ t('pano.kritikOlaylar') }}</h2>
          <UButton to="/olaylar" variant="link" size="sm" trailing-icon="i-lucide-arrow-right" :label="t('genel.tumu')" />
        </div>
        <p v-if="!kritikOlaylar.length" class="flex items-center gap-2 text-sm text-muted">
          <UIcon name="i-lucide-circle-check" class="size-4" />
          {{ t('pano.olayYok') }}
        </p>
        <ul v-else class="grid gap-2.5 sm:grid-cols-2 xl:grid-cols-4">
          <li v-for="o in kritikOlaylar" :key="o.id">
            <NuxtLink
              :to="{ path: '/olaylar', query: { olay: o.id } }"
              class="block h-full rounded-md border border-default seviye-serit bg-default p-3 basilabilir hover:bg-elevated/60"
              :class="`seviye-serit--${o.siddet}`"
            >
              <div class="flex items-start justify-between gap-2">
                <p class="text-sm font-medium text-highlighted line-clamp-2">{{ o.baslik }}</p>
                <SeviyeRozeti :seviye="o.siddet" class="shrink-0" />
              </div>
              <p class="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted">
                <span class="flex items-center gap-1"><UIcon :name="OLAY_TURU_IKONU[o.tur]" class="size-3.5" />{{ t(`olayTuru.${o.tur}`) }}</span>
                <span>{{ t('olay.tedarikciSayisi', { n: o.etkilenenler.length }) }}</span>
                <span v-if="o.toplamMaliyetEtkisiUsd">{{ para(o.toplamMaliyetEtkisiUsd) }}</span>
                <span v-if="o.gecikmeVar" class="flex items-center gap-1 font-medium text-toned">
                  <UIcon name="i-lucide-clock-alert" class="size-3.5" />{{ t('olay.gecikme') }}
                </span>
                <span v-if="o.analizVar" class="flex items-center gap-1 font-medium text-primary">
                  <UIcon name="i-lucide-bot" class="size-3.5" />{{ t('olay.modelCikarimi') }}
                </span>
              </p>
            </NuxtLink>
          </li>
        </ul>
      </UCard>

      <!-- Gösterge + dağılım | harita + ülkeye göre alım -->
      <div class="grid items-start gap-6 xl:grid-cols-[18rem_minmax(0,1fr)]">
        <div class="grid gap-6 sm:grid-cols-2 xl:grid-cols-1 content-start">
          <UCard :ui="{ body: 'p-4 sm:p-5' }">
            <h2 class="font-semibold text-highlighted">{{ t('pano.portfoySkoru') }}</h2>
            <p class="text-sm text-muted mb-2">{{ t('pano.alimAgirlikli') }}</p>
            <GrafikGosterge :skor="portfoy" />
          </UCard>
          <GrafikKart :baslik="t('pano.riskDagilimi')" :aciklama="t('pano.riskDagilimiAcik')" :tablo="dagilimTablosu">
            <GrafikHalka :dilimler="dagilim" :orta-deger="String(tedarikciler.length)" :orta-etiket="t('pano.tedarikciEtiketi')" />
          </GrafikKart>
        </div>

        <div class="grid gap-6 min-w-0">
          <GrafikKart
            :baslik="t('pano.riskHaritasi')"
            :aciklama="t('pano.riskHaritasiAcik')"
            :tablo="haritaTablosu"
          >
            <GrafikRiskHaritasi :tedarikciler="tedarikciler" />
          </GrafikKart>
          <GrafikKart :baslik="t('pano.ulkeAlim')" :aciklama="t('pano.ulkeAlimAcik')" :tablo="ulkeTablosu">
            <GrafikCubuk :cubuklar="ulkeler" />
          </GrafikKart>
        </div>
      </div>
    </div>
  </SayfaPaneli>
</template>
