<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'

const UBadge = resolveComponent('UBadge')
const RiskRozeti = resolveComponent('RiskRozeti')
const { t, para, sayi, tarih } = useDil()

const [{ data: olaylar, error, refresh: olaylariYenile }, { data: tedarikciler }] = await Promise.all([
  useFetch<EtkiliOlay[]>('/api/olaylar', { default: () => [] }),
  useFetch<RiskliTedarikci[]>('/api/tedarikciler', { default: () => [] })
])

// Seçili olay adres çubuğunda tutulur: sayfa yenilenince veya bağlantı paylaşılınca aynı olay açılır
const route = useRoute()
const secili = computed(() =>
  olaylar.value.find(o => o.id === route.query.olay) ?? olaylar.value[0] ?? null
)
// Dar ekranda detay listenin altında kalır; seçilince oraya kaydırılır
const detay = useTemplateRef('detay')
async function sec(id: string) {
  await navigateTo({ query: { olay: id } }, { replace: true })
  if (!window.matchMedia('(min-width: 1024px)').matches) {
    // Hareket hassasiyeti olanlarda kaydırma animasyonsuz
    const azHareket = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    detay.value?.scrollIntoView({ behavior: azHareket ? 'auto' : 'smooth', block: 'start' })
  }
}

// Modelin bu haber için yaptığı çıkarım (yoksa null)
const { data: analiz, status: analizDurumu } = await useFetch<ModelCikarimi | null>(
  () => `/api/olaylar/${secili.value?.id}/analiz`,
  { immediate: Boolean(secili.value), watch: [() => secili.value?.id] }
)

// Yönetici, hatalı veya deneme olayını (çıkarımıyla birlikte) kaldırabilir
const toast = useToast()
const { user } = useUserSession()
const silinecek = ref(false)
async function olayiSil() {
  if (!secili.value) return
  try {
    await $fetch(`/api/olaylar/${secili.value.id}`, { method: 'DELETE' })
    silinecek.value = false
    await navigateTo({ query: {} }, { replace: true })
    await olaylariYenile()
    toast.add({ title: t('olaylar.kaldirildi'), color: 'success', icon: 'i-lucide-check' })
  }
  catch {
    toast.add({ title: t('olaylar.kaldirilamadi'), color: 'error', icon: 'i-lucide-circle-alert' })
  }
}

const riskler = computed(() => new Map(tedarikciler.value.map(x => [x.id, x.risk])))

const maliyetCubuklari = computed(() => [...olaylar.value]
  .sort((a, b) => b.toplamMaliyetEtkisiUsd - a.toplamMaliyetEtkisiUsd)
  .map(o => ({
    ad: o.baslik,
    deger: o.toplamMaliyetEtkisiUsd,
    etiket: para(o.toplamMaliyetEtkisiUsd),
    ayrinti: [
      { ad: t('alan.siddet'), deger: t(`seviye.${o.siddet}`) },
      { ad: t('alan.etkilenen'), deger: o.etkilenenler.map(e => e.firma).join(', ') || '—' }
    ]
  })))
const maliyetTablosu = computed(() => ({
  basliklar: [t('alan.olay'), t('alan.yillikEkMaliyet')],
  satirlar: maliyetCubuklari.value.map(c => [c.ad, c.etiket])
}))

// Kaynak bağlantısı ileride dış veriden gelecek; yalnızca https bağlantılar gösterilir
const kaynakUrl = computed(() => {
  const url = secili.value?.kaynak.url
  return url && url.startsWith('https://') ? url : null
})

const stoguRiskteOlanlar = computed(() => secili.value?.etkilenenler.filter(e => e.stokYetmeyebilir).length ?? 0)

const columns = computed<TableColumn<OlayEtkisi>[]>(() => [
  {
    accessorKey: 'firma',
    header: t('alan.tedarikci'),
    cell: ({ row }) => h('div', [
      h('p', { class: 'font-medium text-highlighted' }, row.original.firma),
      h('p', { class: 'text-xs text-muted' }, row.original.parca)
    ])
  },
  {
    id: 'risk',
    header: t('alan.risk'),
    cell: ({ row }) => {
      const risk = riskler.value.get(row.original.tedarikciId)
      return risk ? h(RiskRozeti, { risk }) : null
    }
  },
  {
    accessorKey: 'maliyetEtkisiUsd',
    header: () => h('div', { class: 'text-right' }, t('alan.ekMaliyet')),
    cell: ({ row }) => h('div', { class: 'text-right tabular-nums' },
      row.original.maliyetEtkisiUsd ? para(row.original.maliyetEtkisiUsd) : '—')
  },
  // Stok sütunu yalnızca gecikme beklenen olaylarda anlamlıdır
  ...(secili.value?.gecikmeVar
    ? [{
        id: 'stok',
        header: t('olaylar.gecikmedeStok'),
        cell: ({ row }: { row: { original: OlayEtkisi } }) => row.original.stokYetmeyebilir
          ? h(UBadge, { label: t('olaylar.yetmeyebilir'), color: 'error', variant: 'subtle', icon: 'i-lucide-triangle-alert' })
          : h('span', { class: 'text-muted' }, t('olaylar.yeterli'))
      }]
    : [])
])
</script>

<template>
  <SayfaPaneli :baslik="t('nav.olaylar')">
    <UAlert
      v-if="error"
      color="error"
      variant="subtle"
      icon="i-lucide-triangle-alert"
      :title="t('olaylar.okunamadi')"
      :description="error.statusMessage"
    />

    <UEmpty
      v-else-if="!secili"
      icon="i-lucide-circle-check"
      :title="t('olaylar.yok')"
      :description="t('olaylar.yokAcik')"
      class="my-auto"
    />

    <div v-else class="space-y-6">
      <GrafikKart :baslik="t('olaylar.maliyetGrafik')" :aciklama="t('olaylar.maliyetGrafikAcik')" :tablo="maliyetTablosu">
        <GrafikCubuk :cubuklar="maliyetCubuklari" etiket-genisligi="16rem" />
      </GrafikKart>

      <div class="grid gap-6 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
        <!-- Olay listesi -->
        <section :aria-label="t('olaylar.aktifOlaylar')" class="space-y-2">
          <p class="text-sm text-muted">{{ t('olaylar.aktifSayi', { n: olaylar.length }) }}</p>
          <OlayKarti
            v-for="o in olaylar"
            :key="o.id"
            :olay="o"
            :secili="o.id === secili.id"
            @sec="sec(o.id)"
          />
        </section>

        <!-- Seçili olay: önce haberin genel bilgileri, ardından modelin çıkarımı -->
        <section ref="detay" :aria-label="t('olaylar.detay')" class="space-y-4 min-w-0 scroll-mt-4">
          <UCard>
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div class="space-y-1">
                <div class="flex flex-wrap items-center gap-2 text-sm text-muted">
                  <span class="flex items-center gap-1">
                    <UIcon :name="OLAY_TURU_IKONU[secili.tur]" class="size-4" />
                    {{ t(`olayTuru.${secili.tur}`) }}
                  </span>
                  <span>·</span>
                  <span>
                    {{ tarih(secili.tarih) }}
                    <template v-if="secili.bitisTarihi">– {{ tarih(secili.bitisTarihi) }}</template>
                    <template v-else>· {{ t('olaylar.suresiz') }}</template>
                  </span>
                </div>
                <h2 class="text-xl font-semibold text-highlighted">{{ secili.baslik }}</h2>
              </div>
              <div class="flex items-center gap-2">
                <UBadge v-if="secili.ornek" color="neutral" variant="outline" icon="i-lucide-flask-conical">
                  {{ t('olaylar.ornek') }}
                </UBadge>
                <SeviyeRozeti :seviye="secili.siddet" buyuk>
                  {{ t('olaylar.siddet', { s: t(`seviye.${secili.siddet}`) }) }}
                </SeviyeRozeti>
                <UButton
                  v-if="user?.rol === 'yonetici'"
                  icon="i-lucide-trash-2"
                  color="neutral"
                  variant="ghost"
                  :aria-label="t('olaylar.kaldir')"
                  @click="silinecek = true"
                />
              </div>
            </div>

            <p class="mt-3 text-default">{{ secili.ozet }}</p>

            <div class="mt-4 flex items-center gap-2 text-sm text-muted">
              <UIcon name="i-lucide-link" class="size-4" />
              <span>{{ t('olaylar.kaynak') }}</span>
              <ULink v-if="kaynakUrl" :to="kaynakUrl" target="_blank" rel="noopener noreferrer" class="text-primary">
                {{ secili.kaynak.ad }}
              </ULink>
              <span v-else>{{ secili.kaynak.ad }}</span>
            </div>
          </UCard>

          <div class="grid gap-3 grid-cols-2 xl:grid-cols-4">
            <UCard :ui="{ body: 'p-3 sm:p-4' }">
              <p class="text-sm text-muted">{{ t('olaylar.etkilenenSayi') }}</p>
              <p class="mt-1 text-xl font-semibold text-highlighted">{{ sayi(secili.etkilenenler.length) }}</p>
            </UCard>
            <UCard :ui="{ body: 'p-3 sm:p-4' }">
              <p class="text-sm text-muted">{{ t('alan.yillikEkMaliyet') }}</p>
              <p class="mt-1 text-xl font-semibold text-highlighted">{{ para(secili.toplamMaliyetEtkisiUsd) }}</p>
            </UCard>
            <!-- Gecikme süresi haberden çıkarılamaz: yalnızca gecikme bekleniyorsa gösterilir -->
            <template v-if="secili.gecikmeVar">
              <UCard :ui="{ body: 'p-3 sm:p-4' }" class="ring-1 ring-[var(--risk-orta)]">
                <p class="text-sm text-muted">{{ t('olaylar.sevkiyat') }}</p>
                <p class="mt-1 flex items-center gap-1.5 text-xl font-semibold text-highlighted">
                  <UIcon name="i-lucide-clock-alert" class="size-5" style="color: var(--risk-orta)" />
                  {{ t('olaylar.gecikmeVar') }}
                </p>
              </UCard>
              <UCard :ui="{ body: 'p-3 sm:p-4' }">
                <p class="text-sm text-muted">{{ t('olaylar.stokRiskte') }}</p>
                <p class="mt-1 text-xl font-semibold text-highlighted">{{ sayi(stoguRiskteOlanlar) }}</p>
              </UCard>
            </template>
          </div>

          <UCard :ui="{ body: 'p-0 sm:p-0' }">
            <template #header>
              <h3 class="font-semibold text-highlighted">{{ t('olaylar.etkilenenler') }}</h3>
            </template>
            <UTable :data="secili.etkilenenler" :columns="columns" :empty="t('olaylar.etkilemiyor')" />
          </UCard>

          <!-- Modelin bu haberden yaptığı çıkarım -->
          <USkeleton v-if="analizDurumu === 'pending' && !analiz" class="h-40 w-full" />
          <ModelAnalizi v-else-if="analiz" :rapor="analiz" :tedarikciler="tedarikciler" />
          <UCard v-else variant="subtle">
            <p class="flex items-center gap-2 text-sm text-muted">
              <UIcon name="i-lucide-bot" class="size-4" />
              {{ t('olaylar.cikarimYok') }}
            </p>
          </UCard>
        </section>
      </div>
    </div>

    <UModal
      v-model:open="silinecek"
      :title="t('olaylar.kaldir')"
      :description="secili ? t('olaylar.kaldirAciklama', { baslik: secili.baslik }) : ''"
    >
      <template #footer>
        <div class="flex justify-end gap-2 w-full">
          <UButton :label="t('genel.vazgec')" color="neutral" variant="ghost" @click="silinecek = false" />
          <UButton :label="t('genel.kaldir')" color="error" @click="olayiSil" />
        </div>
      </template>
    </UModal>
  </SayfaPaneli>
</template>
