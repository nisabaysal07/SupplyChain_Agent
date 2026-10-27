<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'

const UBadge = resolveComponent('UBadge')
const UButton = resolveComponent('UButton')
const UIcon = resolveComponent('UIcon')
const RiskRozeti = resolveComponent('RiskRozeti')

const { data: tedarikciler, status, error } = await useFetch<RiskliTedarikci[]>('/api/tedarikciler', { default: () => [] })
const arama = ref('')
const acikSatirlar = ref({})

// En riskli tedarikçi en üstte
const sirali = computed(() => [...tedarikciler.value].sort((a, b) => b.risk.skor - a.risk.skor))

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
      'ui': { leadingIcon: ['transition-transform', row.getIsExpanded() ? 'rotate-180' : ''] },
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
      <UInput v-model="arama" icon="i-lucide-search" placeholder="Tedarikçi veya parça ara" class="w-64" />
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

      <UTable
        v-model:global-filter="arama"
        v-model:expanded="acikSatirlar"
        :data="sirali"
        :columns="columns"
        :loading="status === 'pending'"
        empty="Kayıt bulunamadı"
        class="border border-default rounded-lg bg-default"
      >
        <template #expanded="{ row }">
          <RiskDokumu :risk="row.original.risk" class="px-2 py-1" />
        </template>
      </UTable>
    </div>
  </SayfaPaneli>
</template>
