<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'

const UBadge = resolveComponent('UBadge')
const UButton = resolveComponent('UButton')
const UIcon = resolveComponent('UIcon')
const RiskRozeti = resolveComponent('RiskRozeti')
const { t, para, sayi, tarih, ulkeAdi } = useDil()

const { data: tedarikciler, status, error } = await useFetch<RiskliTedarikci[]>('/api/tedarikciler', { default: () => [] })
const arama = ref('')
const acikSatirlar = ref({})

// Filtre ve sıralama adres çubuğunda tutulur: Kontrol Paneli'ndeki kutucuklar filtreli bağlantı verir,
// sayfa yenilenince veya bağlantı paylaşılınca aynı liste görünür
const route = useRoute()
const router = useRouter()
function sorguSecimi<T extends string>(ad: string, gecerli: readonly T[], varsayilan: () => T) {
  return computed<T>({
    get: () => {
      const deger = route.query[ad]
      return gecerli.includes(deger as T) ? deger as T : varsayilan()
    },
    set: (deger) => {
      router.replace({ query: { ...route.query, [ad]: deger === varsayilan() ? undefined : deger } })
    }
  })
}

type SiralamaAnahtari = 'risk' | 'alim' | 'stok' | 'olay' | 'sozlesme' | 'rota' | 'ad'
type Yon = 'artan' | 'azalan'
// Her sıralamanın doğal yönü: en önemli olan üstte (ör. stokta en kritik, sözleşmede en yakın bitiş)
const SIRALAMALAR: Record<SiralamaAnahtari, { deger: (x: RiskliTedarikci) => number | string, yon: Yon }> = {
  risk: { deger: x => x.risk.skor, yon: 'azalan' },
  alim: { deger: x => x.yillikAlimUsd, yon: 'azalan' },
  stok: { deger: x => x.stok.kullanilabilir / Math.max(1, x.stok.siparisSeviyesi), yon: 'artan' },
  olay: { deger: x => x.risk.olayIdleri.length, yon: 'azalan' },
  sozlesme: { deger: x => x.sozlesmeBitis, yon: 'artan' },
  rota: { deger: x => x.rota.transitGun, yon: 'azalan' },
  ad: { deger: x => x.firma, yon: 'artan' }
}
const siralama = sorguSecimi('sirala', Object.keys(SIRALAMALAR) as SiralamaAnahtari[], () => 'risk')
const yon = sorguSecimi<Yon>('yon', ['artan', 'azalan'], () => SIRALAMALAR[siralama.value].yon)
const siralamaSecenekleri = computed(() => Object.keys(SIRALAMALAR).map(value => ({ label: t(`ted.sirala.${value}`), value })))

const riskFiltresi = sorguSecimi('risk', ['tumu', 'yuksek', 'orta', 'dusuk'] as const, () => 'tumu')
const stokFiltresi = sorguSecimi('stok', ['tumu', 'siparis_gerekli', 'yeterli'] as const, () => 'tumu')
const olayFiltresi = sorguSecimi('olay', ['tumu', 'var', 'yok'] as const, () => 'tumu')
const riskSecenekleri = computed(() => [
  { label: t('ted.tumRiskler'), value: 'tumu' },
  { label: t('seviyeRisk.yuksek'), value: 'yuksek' },
  { label: t('seviyeRisk.orta'), value: 'orta' },
  { label: t('seviyeRisk.dusuk'), value: 'dusuk' }
])
const stokSecenekleri = computed(() => [
  { label: t('ted.tumStok'), value: 'tumu' },
  { label: t('ted.siparisGerekli'), value: 'siparis_gerekli' },
  { label: t('ted.stokYeterli'), value: 'yeterli' }
])
const olaySecenekleri = computed(() => [
  { label: t('ted.olayHepsi'), value: 'tumu' },
  { label: t('ted.olayVar'), value: 'var' },
  { label: t('ted.olayYok'), value: 'yok' }
])
const filtreVar = computed(() => [riskFiltresi, stokFiltresi, olayFiltresi].some(f => f.value !== 'tumu'))
function filtreleriTemizle() {
  const { risk: _r, stok: _s, olay: _o, ...kalan } = route.query
  router.replace({ query: kalan })
  arama.value = ''
}

const sirali = computed(() => {
  const s = SIRALAMALAR[siralama.value]
  const carpan = yon.value === 'artan' ? 1 : -1
  const aranan = arama.value.trim().toLocaleLowerCase('tr')
  return tedarikciler.value
    // Ülke hem kayıtlı adıyla hem arayüz dilindeki adıyla aranabilir (Çin / China)
    .filter(x => !aranan || [x.firma, x.firmaResmiAd, x.parca, x.menseUlke, ulkeAdi(x.menseUlke)].some(m => m.toLocaleLowerCase('tr').includes(aranan)))
    .filter(x => riskFiltresi.value === 'tumu' || x.risk.seviye === riskFiltresi.value)
    .filter(x => stokFiltresi.value === 'tumu' || x.stok.durum === stokFiltresi.value)
    .filter(x => olayFiltresi.value === 'tumu' || (x.risk.olayIdleri.length > 0) === (olayFiltresi.value === 'var'))
    .sort((a, b) => {
      const x = s.deger(a)
      const y = s.deger(b)
      const fark = typeof x === 'string' ? x.localeCompare(String(y), 'tr') : x - (y as number)
      // Eşitlikte en riskli üstte
      return carpan * fark || b.risk.skor - a.risk.skor
    })
})

// Kontrol Paneli'nden filtreli gelindiyse liste, grafiğin altında kalmasın
const liste = useTemplateRef('liste')
onMounted(() => {
  if (filtreVar.value) liste.value?.scrollIntoView({ block: 'start' })
})

const stokTablosu = computed(() => ({
  basliklar: [t('alan.parca'), t('ted.kullanilabilir'), t('ted.yetiyor'), t('ted.gereken'), t('alan.durum')],
  satirlar: tedarikciler.value.map((x) => {
    const gunluk = x.yillikAdet / 365
    return [
      x.parca,
      sayi(x.stok.kullanilabilir),
      String(Math.round(x.stok.kullanilabilir / gunluk)),
      String(Math.round(x.stok.siparisSeviyesi / gunluk)),
      t(x.stok.durum === 'siparis_gerekli' ? 'ted.siparisGerekli' : 'ted.yeterli')
    ]
  })
}))

const columns = computed<TableColumn<RiskliTedarikci>[]>(() => [
  {
    id: 'ac',
    cell: ({ row }) => h(UButton, {
      'color': 'neutral',
      'variant': 'ghost',
      'size': 'sm',
      'icon': 'i-lucide-chevron-down',
      'aria-label': t(row.getIsExpanded() ? 'ted.dokumGizle' : 'ted.dokumGoster'),
      'ui': { leadingIcon: ['transition-transform duration-200 ease-in-out',row.getIsExpanded() ? 'rotate-180' : ''] },
      'onClick': () => row.toggleExpanded()
    })
  },
  {
    accessorKey: 'firma',
    header: t('alan.tedarikci'),
    cell: ({ row }) => h('div', [
      h('p', { class: 'font-medium text-highlighted' }, row.original.firma),
      h('p', { class: 'text-xs text-muted' }, row.original.firmaResmiAd)
    ])
  },
  { accessorKey: 'parca', header: t('alan.parca') },
  {
    id: 'risk',
    header: t('alan.risk'),
    cell: ({ row }) => h(RiskRozeti, { risk: row.original.risk })
  },
  {
    accessorKey: 'menseUlke',
    header: t('alan.mense'),
    cell: ({ row }) => h('div', { class: 'flex items-center gap-1.5' }, [
      ulkeAdi(row.original.menseUlke),
      row.original.anlasmaVar
        ? h(UBadge, { label: t('ted.sta'), color: 'success', variant: 'subtle', size: 'sm' })
        : null
    ])
  },
  {
    id: 'rota',
    header: t('alan.rota'),
    cell: ({ row }) => h('div', { class: 'flex items-center gap-1.5' }, [
      h(UIcon, { name: row.original.rota.mod === 'hava' ? 'i-lucide-plane' : 'i-lucide-ship', class: 'size-4 text-muted' }),
      t('genel.gun', { n: row.original.rota.transitGun })
    ])
  },
  {
    accessorKey: 'yillikAlimUsd',
    header: () => h('div', { class: 'text-right' }, t('alan.yillikAlim')),
    cell: ({ row }) => h('div', { class: 'text-right tabular-nums' }, para(row.original.yillikAlimUsd))
  },
  {
    id: 'stok',
    header: t('alan.stok'),
    cell: ({ row }) => {
      const s = row.original.stok
      return h(UBadge, {
        label: t(s.durum === 'siparis_gerekli' ? 'ted.siparisGerekli' : 'ted.yeterli'),
        color: s.durum === 'siparis_gerekli' ? 'warning' : 'neutral',
        variant: 'subtle',
        title: t('ted.stokBaslik', { a: sayi(s.kullanilabilir), b: sayi(s.siparisSeviyesi) })
      })
    }
  },
  {
    accessorKey: 'sozlesmeBitis',
    header: t('alan.sozlesmeBitis'),
    cell: ({ row }) => tarih(row.original.sozlesmeBitis)
  }
])
</script>

<template>
  <SayfaPaneli :baslik="t('nav.tedarikciler')">
    <template #sag>
      <!-- Dar ekranda başlığı ezmesin diye arama kutusu filtrelerin üstüne taşınır -->
      <UInput v-model="arama" icon="i-lucide-search" :placeholder="t('ted.ara')" :aria-label="t('ted.ara')" class="hidden sm:inline-flex w-64" />
    </template>

    <UAlert
      v-if="error"
      color="error"
      variant="subtle"
      icon="i-lucide-triangle-alert"
      :title="t('ted.okunamadi')"
      :description="error.statusMessage"
    />

    <div v-else class="space-y-6">
      <GrafikKart
        :baslik="t('ted.stokGrafik')"
        :aciklama="t('ted.stokGrafikAcik')"
        :tablo="stokTablosu"
      >
        <GrafikStokKapsami :tedarikciler="tedarikciler" />
      </GrafikKart>

      <section ref="liste" :aria-label="t('ted.liste')" class="space-y-3 scroll-mt-4">
        <!-- Filtreler ve sıralama -->
        <div class="flex flex-wrap items-center gap-2">
          <UInput v-model="arama" icon="i-lucide-search" :placeholder="t('ted.ara')" :aria-label="t('ted.ara')" class="w-full sm:hidden" />
          <USelect v-model="riskFiltresi" :items="riskSecenekleri" :aria-label="t('ted.riskFiltre')" class="w-full sm:w-40" />
          <USelect v-model="stokFiltresi" :items="stokSecenekleri" :aria-label="t('ted.stokFiltre')" class="w-full sm:w-48" />
          <USelect v-model="olayFiltresi" :items="olaySecenekleri" :aria-label="t('ted.olayFiltre')" class="w-full sm:w-52" />
          <UButton
            v-if="filtreVar || arama"
            color="neutral"
            variant="ghost"
            icon="i-lucide-x"
            :label="t('ted.temizle')"
            @click="filtreleriTemizle"
          />

          <div class="flex w-full items-center gap-2 sm:ms-auto sm:w-auto">
            <span class="text-sm text-muted shrink-0">{{ t('ted.siralaEtiket') }}</span>
            <USelect v-model="siralama" :items="siralamaSecenekleri" :aria-label="t('ted.siralamaOlcutu')" class="min-w-0 flex-1 sm:w-44 sm:flex-none" />
            <UButton
              color="neutral"
              variant="outline"
              :icon="yon === 'azalan' ? 'i-lucide-arrow-down-wide-narrow' : 'i-lucide-arrow-up-narrow-wide'"
              :label="t(yon === 'azalan' ? 'ted.azalan' : 'ted.artan')"
              :aria-label="t('ted.yonEtiket', { yon: t(yon === 'azalan' ? 'ted.azalan' : 'ted.artan') })"
              @click="yon = yon === 'azalan' ? 'artan' : 'azalan'"
            />
          </div>
        </div>
        <p class="text-sm text-muted" aria-live="polite">
          {{ t('ted.sayac', { a: sirali.length, b: tedarikciler.length }) }}
        </p>

        <UTable
          v-model:expanded="acikSatirlar"
          :data="sirali"
          :columns="columns"
          :loading="status === 'pending'"
          :empty="t('ted.bos')"
          class="border border-default rounded-lg bg-default"
        >
          <template #expanded="{ row }">
            <RiskDokumu :risk="row.original.risk" class="px-2 py-1" />
          </template>
        </UTable>
      </section>
    </div>
  </SayfaPaneli>
</template>
