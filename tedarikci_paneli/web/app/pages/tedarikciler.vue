<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'

const UBadge = resolveComponent('UBadge')
const UButton = resolveComponent('UButton')
const UIcon = resolveComponent('UIcon')
const RiskRozeti = resolveComponent('RiskRozeti')

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
const SIRALAMALAR: Record<SiralamaAnahtari, { etiket: string, deger: (t: RiskliTedarikci) => number | string, yon: Yon }> = {
  risk: { etiket: 'Risk skoru', deger: t => t.risk.skor, yon: 'azalan' },
  alim: { etiket: 'Yıllık alım', deger: t => t.yillikAlimUsd, yon: 'azalan' },
  stok: { etiket: 'Stok yeterliliği', deger: t => t.stok.kullanilabilir / Math.max(1, t.stok.siparisSeviyesi), yon: 'artan' },
  olay: { etiket: 'Bağlı olay sayısı', deger: t => t.risk.olayIdleri.length, yon: 'azalan' },
  sozlesme: { etiket: 'Sözleşme bitişi', deger: t => t.sozlesmeBitis, yon: 'artan' },
  rota: { etiket: 'Yol süresi', deger: t => t.rota.transitGun, yon: 'azalan' },
  ad: { etiket: 'Tedarikçi adı', deger: t => t.firma, yon: 'artan' }
}
const siralama = sorguSecimi('sirala', Object.keys(SIRALAMALAR) as SiralamaAnahtari[], () => 'risk')
const yon = sorguSecimi<Yon>('yon', ['artan', 'azalan'], () => SIRALAMALAR[siralama.value].yon)
const siralamaSecenekleri = Object.entries(SIRALAMALAR).map(([value, s]) => ({ label: s.etiket, value }))

const riskFiltresi = sorguSecimi('risk', ['tumu', 'yuksek', 'orta', 'dusuk'] as const, () => 'tumu')
const stokFiltresi = sorguSecimi('stok', ['tumu', 'siparis_gerekli', 'yeterli'] as const, () => 'tumu')
const olayFiltresi = sorguSecimi('olay', ['tumu', 'var', 'yok'] as const, () => 'tumu')
const riskSecenekleri = [
  { label: 'Tüm riskler', value: 'tumu' },
  { label: 'Yüksek risk', value: 'yuksek' },
  { label: 'Orta risk', value: 'orta' },
  { label: 'Düşük risk', value: 'dusuk' }
]
const stokSecenekleri = [
  { label: 'Tüm stok durumları', value: 'tumu' },
  { label: 'Sipariş gerekli', value: 'siparis_gerekli' },
  { label: 'Stok yeterli', value: 'yeterli' }
]
const olaySecenekleri = [
  { label: 'Olay bağlantısı: hepsi', value: 'tumu' },
  { label: 'Bir olayla bağlantılı', value: 'var' },
  { label: 'Olay bağlantısı yok', value: 'yok' }
]
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
    .filter(t => !aranan || [t.firma, t.firmaResmiAd, t.parca, t.menseUlke].some(m => m.toLocaleLowerCase('tr').includes(aranan)))
    .filter(t => riskFiltresi.value === 'tumu' || t.risk.seviye === riskFiltresi.value)
    .filter(t => stokFiltresi.value === 'tumu' || t.stok.durum === stokFiltresi.value)
    .filter(t => olayFiltresi.value === 'tumu' || (t.risk.olayIdleri.length > 0) === (olayFiltresi.value === 'var'))
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
  basliklar: ['Parça', 'Kullanılabilir (adet)', 'Stok yetiyor (gün)', 'Gereken (gün)', 'Durum'],
  satirlar: tedarikciler.value.map((t) => {
    const gunluk = t.yillikAdet / 365
    return [
      t.parca,
      sayiBicimi(t.stok.kullanilabilir),
      String(Math.round(t.stok.kullanilabilir / gunluk)),
      String(Math.round(t.stok.siparisSeviyesi / gunluk)),
      t.stok.durum === 'siparis_gerekli' ? 'Sipariş gerekli' : 'Yeterli'
    ]
  })
}))

const columns: TableColumn<RiskliTedarikci>[] = [
  {
    id: 'ac',
    cell: ({ row }) => h(UButton, {
      'color': 'neutral',
      'variant': 'ghost',
      'size': 'sm',
      'icon': 'i-lucide-chevron-down',
      'aria-label': row.getIsExpanded() ? 'Risk dökümünü gizle' : 'Risk dökümünü göster',
      'ui': { leadingIcon: ['transition-transform duration-200 ease-in-out',row.getIsExpanded() ? 'rotate-180' : ''] },
      'onClick': () => row.toggleExpanded()
    })
  },
  {
    accessorKey: 'firma',
    header: 'Tedarikçi',
    cell: ({ row }) => h('div', [
      h('p', { class: 'font-medium text-highlighted' }, row.original.firma),
      h('p', { class: 'text-xs text-muted' }, row.original.firmaResmiAd)
    ])
  },
  { accessorKey: 'parca', header: 'Parça' },
  {
    id: 'risk',
    header: 'Risk',
    cell: ({ row }) => h(RiskRozeti, { risk: row.original.risk })
  },
  {
    accessorKey: 'menseUlke',
    header: 'Menşe',
    cell: ({ row }) => h('div', { class: 'flex items-center gap-1.5' }, [
      row.original.menseUlke,
      row.original.anlasmaVar
        ? h(UBadge, { label: 'STA', color: 'success', variant: 'subtle', size: 'sm' })
        : null
    ])
  },
  {
    id: 'rota',
    header: 'Rota',
    cell: ({ row }) => h('div', { class: 'flex items-center gap-1.5' }, [
      h(UIcon, { name: row.original.rota.mod === 'hava' ? 'i-lucide-plane' : 'i-lucide-ship', class: 'size-4 text-muted' }),
      `${row.original.rota.transitGun} gün`
    ])
  },
  {
    accessorKey: 'yillikAlimUsd',
    header: () => h('div', { class: 'text-right' }, 'Yıllık alım'),
    cell: ({ row }) => h('div', { class: 'text-right tabular-nums' }, paraBicimi(row.original.yillikAlimUsd))
  },
  {
    id: 'stok',
    header: 'Stok',
    cell: ({ row }) => {
      const s = row.original.stok
      return h(UBadge, {
        label: s.durum === 'siparis_gerekli' ? 'Sipariş gerekli' : 'Yeterli',
        color: s.durum === 'siparis_gerekli' ? 'warning' : 'neutral',
        variant: 'subtle',
        title: `Kullanılabilir ${sayiBicimi(s.kullanilabilir)} · sipariş seviyesi ${sayiBicimi(s.siparisSeviyesi)}`
      })
    }
  },
  {
    accessorKey: 'sozlesmeBitis',
    header: 'Sözleşme bitişi',
    cell: ({ row }) => tarihBicimi(row.original.sozlesmeBitis)
  }
]
</script>

<template>
  <SayfaPaneli baslik="Tedarikçiler">
    <template #sag>
      <!-- Dar ekranda başlığı ezmesin diye arama kutusu filtrelerin üstüne taşınır -->
      <UInput v-model="arama" icon="i-lucide-search" placeholder="Tedarikçi veya parça ara" class="hidden sm:inline-flex w-64" />
    </template>

    <UAlert
      v-if="error"
      color="error"
      variant="subtle"
      icon="i-lucide-triangle-alert"
      title="Tedarikçi verisi okunamadı"
      :description="error.statusMessage"
    />

    <div v-else class="space-y-6">
      <GrafikKart
        baslik="Stok kaç gün yetiyor?"
        aciklama="Kullanılabilir stok ile yeniden sipariş için gereken süre; en kritik parça üstte"
        :tablo="stokTablosu"
      >
        <GrafikStokKapsami :tedarikciler="tedarikciler" />
      </GrafikKart>

      <section ref="liste" aria-label="Tedarikçi listesi" class="space-y-3 scroll-mt-4">
        <!-- Filtreler ve sıralama -->
        <div class="flex flex-wrap items-center gap-2">
          <UInput v-model="arama" icon="i-lucide-search" placeholder="Tedarikçi veya parça ara" aria-label="Tedarikçi veya parça ara" class="w-full sm:hidden" />
          <USelect v-model="riskFiltresi" :items="riskSecenekleri" aria-label="Risk seviyesine göre filtrele" class="w-full sm:w-40" />
          <USelect v-model="stokFiltresi" :items="stokSecenekleri" aria-label="Stok durumuna göre filtrele" class="w-full sm:w-48" />
          <USelect v-model="olayFiltresi" :items="olaySecenekleri" aria-label="Olay bağlantısına göre filtrele" class="w-full sm:w-52" />
          <UButton
            v-if="filtreVar || arama"
            color="neutral"
            variant="ghost"
            icon="i-lucide-x"
            label="Filtreleri temizle"
            @click="filtreleriTemizle"
          />

          <div class="flex w-full items-center gap-2 sm:ms-auto sm:w-auto">
            <span class="text-sm text-muted shrink-0">Sırala:</span>
            <USelect v-model="siralama" :items="siralamaSecenekleri" aria-label="Sıralama ölçütü" class="min-w-0 flex-1 sm:w-44 sm:flex-none" />
            <UButton
              color="neutral"
              variant="outline"
              :icon="yon === 'azalan' ? 'i-lucide-arrow-down-wide-narrow' : 'i-lucide-arrow-up-narrow-wide'"
              :label="yon === 'azalan' ? 'Azalan' : 'Artan'"
              :aria-label="`Sıralama yönü: ${yon === 'azalan' ? 'azalan' : 'artan'}. Değiştirmek için tıklayın`"
              @click="yon = yon === 'azalan' ? 'artan' : 'azalan'"
            />
          </div>
        </div>
        <p class="text-sm text-muted" aria-live="polite">
          {{ sirali.length }} / {{ tedarikciler.length }} tedarikçi
        </p>

        <UTable
          v-model:expanded="acikSatirlar"
          :data="sirali"
          :columns="columns"
          :loading="status === 'pending'"
          empty="Bu filtrelere uyan tedarikçi yok"
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
