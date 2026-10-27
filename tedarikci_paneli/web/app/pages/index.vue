<script setup lang="ts">
// Bütün görseller /api/tedarikciler ve /api/olaylar verisinden türetilir; ek veritabanı sorgusu gerekmez
const [{ data: tedarikciler }, { data: olaylar }] = await Promise.all([
  useFetch<RiskliTedarikci[]>('/api/tedarikciler', { default: () => [] }),
  useFetch<EtkiliOlay[]>('/api/olaylar', { default: () => [] })
])

const portfoy = computed(() => portfoySkoru(tedarikciler.value))
const SEVIYELER = ['yuksek', 'orta', 'dusuk'] as const
const SEVIYE_IKONU: Record<Seviye, string> = {
  dusuk: 'i-lucide-circle-check', orta: 'i-lucide-circle-alert', yuksek: 'i-lucide-triangle-alert'
}

const ozet = computed(() => {
  const liste = tedarikciler.value
  return [
    {
      baslik: 'Yüksek riskli tedarikçi',
      deger: sayiBicimi(liste.filter(x => x.risk.seviye === 'yuksek').length),
      alt: `${sayiBicimi(liste.length)} tedarikçiden`,
      icon: 'i-lucide-shield-alert',
      to: { path: '/tedarikciler', query: { risk: 'yuksek' } }
    },
    {
      baslik: 'Aktif olay',
      deger: sayiBicimi(olaylar.value.length),
      alt: `${olaylar.value.filter(o => o.siddet === 'yuksek').length} yüksek şiddetli · ${olaylar.value.filter(o => o.gecikmeVar).length} gecikmeli`,
      icon: 'i-lucide-circle-alert',
      to: { path: '/olaylar' }
    },
    {
      baslik: 'Olayların yıllık ek maliyeti',
      deger: paraBicimi(olaylar.value.reduce((t, o) => t + o.toplamMaliyetEtkisiUsd, 0)),
      alt: `yıllık alımın %${((olaylar.value.reduce((t, o) => t + o.toplamMaliyetEtkisiUsd, 0) / Math.max(1, liste.reduce((t, x) => t + x.yillikAlimUsd, 0))) * 100).toFixed(1)}'i`,
      icon: 'i-lucide-wallet',
      // Olaylar sayfası "olaylara göre yıllık ek maliyet" grafiğiyle açılır
      to: { path: '/olaylar' }
    },
    {
      baslik: 'Sipariş gereken parça',
      deger: sayiBicimi(liste.filter(x => x.stok.durum === 'siparis_gerekli').length),
      alt: 'stok, sipariş seviyesinin altında',
      icon: 'i-lucide-package-open',
      to: { path: '/tedarikciler', query: { stok: 'siparis_gerekli', sirala: 'stok' } }
    }
  ]
})

// Risk dağılımı (halka)
const dagilim = computed(() => SEVIYELER.map(s => ({
  ad: SEVIYE_ETIKETI[s],
  deger: tedarikciler.value.filter(t => t.risk.seviye === s).length,
  renk: SEVIYE_VIZ_RENGI[s],
  ikon: SEVIYE_IKONU[s]
})))

// Menşe ülkeye göre yıllık alım (çubuk)
const ulkeler = computed(() => {
  const gruplar = new Map<string, RiskliTedarikci[]>()
  for (const t of tedarikciler.value) gruplar.set(t.menseUlke, [...(gruplar.get(t.menseUlke) ?? []), t])
  return [...gruplar.entries()]
    .map(([ulke, liste]) => {
      const alim = liste.reduce((t, x) => t + x.yillikAlimUsd, 0)
      return {
        ad: ulke,
        deger: alim,
        etiket: paraBicimi(alim),
        ayrinti: [
          { ad: 'Tedarikçi', deger: liste.map(x => x.firma).join(', ') },
          { ad: 'Ortalama risk', deger: sayiBicimi(Math.round(portfoySkoru(liste))) }
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
  basliklar: ['Seviye', 'Tedarikçi'],
  satirlar: dagilim.value.map(d => [d.ad, String(d.deger)])
}))
const haritaTablosu = computed(() => ({
  basliklar: ['Tedarikçi', 'Çıkış', 'Varış', 'Yıllık alım', 'Risk'],
  satirlar: [...tedarikciler.value].sort((a, b) => b.risk.skor - a.risk.skor).map(t => [
    `${t.firma} · ${t.parca}`, t.rota.cikis, t.rota.varis, paraBicimi(t.yillikAlimUsd), `${t.risk.skor} · ${SEVIYE_ETIKETI[t.risk.seviye]}`
  ])
}))
const ulkeTablosu = computed(() => ({
  basliklar: ['Menşe ülke', 'Yıllık alım'],
  satirlar: ulkeler.value.map(u => [u.ad, u.etiket])
}))
</script>

<template>
  <SayfaPaneli baslik="Kontrol Paneli">
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
          <h2 class="font-semibold text-highlighted">En kritik olaylar</h2>
          <UButton to="/olaylar" variant="link" size="sm" trailing-icon="i-lucide-arrow-right" label="Tümü" />
        </div>
        <p v-if="!kritikOlaylar.length" class="flex items-center gap-2 text-sm text-muted">
          <UIcon name="i-lucide-circle-check" class="size-4" />
          Aktif olay yok. Model yeni bir haber gönderdiğinde burada görünecek.
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
                <span class="flex items-center gap-1"><UIcon :name="OLAY_TURU[o.tur].icon" class="size-3.5" />{{ OLAY_TURU[o.tur].etiket }}</span>
                <span>{{ o.etkilenenler.length }} tedarikçi</span>
                <span v-if="o.toplamMaliyetEtkisiUsd">{{ paraBicimi(o.toplamMaliyetEtkisiUsd) }}</span>
                <span v-if="o.gecikmeVar" class="flex items-center gap-1 font-medium text-toned">
                  <UIcon name="i-lucide-clock-alert" class="size-3.5" />Gecikme
                </span>
                <span v-if="o.analizVar" class="flex items-center gap-1 font-medium text-primary">
                  <UIcon name="i-lucide-bot" class="size-3.5" />Model çıkarımı
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
            <h2 class="font-semibold text-highlighted">Genel portföy risk skoru</h2>
            <p class="text-sm text-muted mb-2">Yıllık alımla ağırlıklı</p>
            <GrafikGosterge :skor="portfoy" />
          </UCard>
          <GrafikKart baslik="Risk dağılımı" aciklama="Tedarikçilerin risk seviyesi" :tablo="dagilimTablosu">
            <GrafikHalka :dilimler="dagilim" :orta-deger="String(tedarikciler.length)" orta-etiket="tedarikçi" />
          </GrafikKart>
        </div>

        <div class="grid gap-6 min-w-0">
          <GrafikKart
            baslik="Risk haritası"
            aciklama="Tedarikçilerin çıkış noktaları ve Türkiye'ye rotaları"
            :tablo="haritaTablosu"
          >
            <GrafikRiskHaritasi :tedarikciler="tedarikciler" />
          </GrafikKart>
          <GrafikKart baslik="Menşe ülkeye göre yıllık alım" aciklama="Hangi ülkeye ne kadar bağımlıyız" :tablo="ulkeTablosu">
            <GrafikCubuk :cubuklar="ulkeler" />
          </GrafikKart>
        </div>
      </div>
    </div>
  </SayfaPaneli>
</template>
