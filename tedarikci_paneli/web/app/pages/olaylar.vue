<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'

const UBadge = resolveComponent('UBadge')
const RiskRozeti = resolveComponent('RiskRozeti')

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
    toast.add({ title: 'Olay kaldırıldı', color: 'success', icon: 'i-lucide-check' })
  }
  catch {
    toast.add({ title: 'Olay kaldırılamadı', color: 'error', icon: 'i-lucide-circle-alert' })
  }
}

const riskler = computed(() => new Map(tedarikciler.value.map(t => [t.id, t.risk])))

const maliyetCubuklari = computed(() => [...olaylar.value]
  .sort((a, b) => b.toplamMaliyetEtkisiUsd - a.toplamMaliyetEtkisiUsd)
  .map(o => ({
    ad: o.baslik,
    deger: o.toplamMaliyetEtkisiUsd,
    etiket: paraBicimi(o.toplamMaliyetEtkisiUsd),
    ayrinti: [
      { ad: 'Şiddet', deger: SEVIYE_ETIKETI[o.siddet] },
      { ad: 'Etkilenen', deger: o.etkilenenler.map(e => e.firma).join(', ') || '—' }
    ]
  })))
const maliyetTablosu = computed(() => ({
  basliklar: ['Olay', 'Yıllık ek maliyet'],
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
    header: 'Tedarikçi',
    cell: ({ row }) => h('div', [
      h('p', { class: 'font-medium text-highlighted' }, row.original.firma),
      h('p', { class: 'text-xs text-muted' }, row.original.parca)
    ])
  },
  {
    id: 'risk',
    header: 'Risk',
    cell: ({ row }) => {
      const risk = riskler.value.get(row.original.tedarikciId)
      return risk ? h(RiskRozeti, { risk }) : null
    }
  },
  {
    accessorKey: 'maliyetEtkisiUsd',
    header: () => h('div', { class: 'text-right' }, 'Ek maliyet'),
    cell: ({ row }) => h('div', { class: 'text-right tabular-nums' },
      row.original.maliyetEtkisiUsd ? paraBicimi(row.original.maliyetEtkisiUsd) : '—')
  },
  // Stok sütunu yalnızca gecikme beklenen olaylarda anlamlıdır
  ...(secili.value?.gecikmeVar
    ? [{
        id: 'stok',
        header: 'Gecikmede stok',
        cell: ({ row }: { row: { original: OlayEtkisi } }) => row.original.stokYetmeyebilir
          ? h(UBadge, { label: 'Yetmeyebilir', color: 'error', variant: 'subtle', icon: 'i-lucide-triangle-alert' })
          : h('span', { class: 'text-muted' }, 'Yeterli')
      }]
    : [])
])
</script>

<template>
  <SayfaPaneli baslik="Olaylar">
    <UAlert
      v-if="error"
      color="error"
      variant="subtle"
      icon="i-lucide-triangle-alert"
      title="Olaylar okunamadı"
      :description="error.statusMessage"
    />

    <UEmpty
      v-else-if="!secili"
      icon="i-lucide-circle-check"
      title="Aktif olay yok"
      description="Model yeni bir haber gönderdiğinde burada listelenecek."
      class="my-auto"
    />

    <div v-else class="space-y-6">
      <GrafikKart baslik="Olaylara göre yıllık ek maliyet" aciklama="Ek vergi veya fiyat artışının yıllık alıma etkisi" :tablo="maliyetTablosu">
        <GrafikCubuk :cubuklar="maliyetCubuklari" etiket-genisligi="16rem" />
      </GrafikKart>

      <div class="grid gap-6 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
        <!-- Olay listesi -->
        <section aria-label="Aktif olaylar" class="space-y-2">
          <p class="text-sm text-muted">{{ olaylar.length }} aktif olay</p>
          <OlayKarti
            v-for="o in olaylar"
            :key="o.id"
            :olay="o"
            :secili="o.id === secili.id"
            @sec="sec(o.id)"
          />
        </section>

        <!-- Seçili olay: önce haberin genel bilgileri, ardından modelin çıkarımı -->
        <section ref="detay" aria-label="Olay detayı" class="space-y-4 min-w-0 scroll-mt-4">
          <UCard>
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div class="space-y-1">
                <div class="flex flex-wrap items-center gap-2 text-sm text-muted">
                  <span class="flex items-center gap-1">
                    <UIcon :name="OLAY_TURU[secili.tur].icon" class="size-4" />
                    {{ OLAY_TURU[secili.tur].etiket }}
                  </span>
                  <span>·</span>
                  <span>
                    {{ tarihBicimi(secili.tarih) }}
                    <template v-if="secili.bitisTarihi">– {{ tarihBicimi(secili.bitisTarihi) }}</template>
                    <template v-else>· süresiz</template>
                  </span>
                </div>
                <h2 class="text-xl font-semibold text-highlighted">{{ secili.baslik }}</h2>
              </div>
              <div class="flex items-center gap-2">
                <UBadge v-if="secili.ornek" color="neutral" variant="outline" icon="i-lucide-flask-conical">
                  Örnek olay
                </UBadge>
                <SeviyeRozeti :seviye="secili.siddet" buyuk>
                  Şiddet: {{ SEVIYE_ETIKETI[secili.siddet] }}
                </SeviyeRozeti>
                <UButton
                  v-if="user?.rol === 'yonetici'"
                  icon="i-lucide-trash-2"
                  color="neutral"
                  variant="ghost"
                  aria-label="Olayı kaldır"
                  @click="silinecek = true"
                />
              </div>
            </div>

            <p class="mt-3 text-default">{{ secili.ozet }}</p>

            <div class="mt-4 flex items-center gap-2 text-sm text-muted">
              <UIcon name="i-lucide-link" class="size-4" />
              <span>Kaynak:</span>
              <ULink v-if="kaynakUrl" :to="kaynakUrl" target="_blank" rel="noopener noreferrer" class="text-primary">
                {{ secili.kaynak.ad }}
              </ULink>
              <span v-else>{{ secili.kaynak.ad }}</span>
            </div>
          </UCard>

          <div class="grid gap-3 grid-cols-2 xl:grid-cols-4">
            <UCard :ui="{ body: 'p-3 sm:p-4' }">
              <p class="text-sm text-muted">Etkilenen tedarikçi</p>
              <p class="mt-1 text-xl font-semibold text-highlighted">{{ sayiBicimi(secili.etkilenenler.length) }}</p>
            </UCard>
            <UCard :ui="{ body: 'p-3 sm:p-4' }">
              <p class="text-sm text-muted">Yıllık ek maliyet</p>
              <p class="mt-1 text-xl font-semibold text-highlighted">{{ paraBicimi(secili.toplamMaliyetEtkisiUsd) }}</p>
            </UCard>
            <!-- Gecikme süresi haberden çıkarılamaz: yalnızca gecikme bekleniyorsa gösterilir -->
            <template v-if="secili.gecikmeVar">
              <UCard :ui="{ body: 'p-3 sm:p-4' }" class="ring-1 ring-[var(--risk-orta)]">
                <p class="text-sm text-muted">Sevkiyat</p>
                <p class="mt-1 flex items-center gap-1.5 text-xl font-semibold text-highlighted">
                  <UIcon name="i-lucide-clock-alert" class="size-5" style="color: var(--risk-orta)" />
                  Gecikme var
                </p>
              </UCard>
              <UCard :ui="{ body: 'p-3 sm:p-4' }">
                <p class="text-sm text-muted">Stoğu risk altında</p>
                <p class="mt-1 text-xl font-semibold text-highlighted">{{ sayiBicimi(stoguRiskteOlanlar) }}</p>
              </UCard>
            </template>
          </div>

          <UCard :ui="{ body: 'p-0 sm:p-0' }">
            <template #header>
              <h3 class="font-semibold text-highlighted">Etkilenen tedarikçiler</h3>
            </template>
            <UTable :data="secili.etkilenenler" :columns="columns" empty="Bu olay hiçbir tedarikçiyi etkilemiyor" />
          </UCard>

          <!-- Modelin bu haberden yaptığı çıkarım -->
          <USkeleton v-if="analizDurumu === 'pending' && !analiz" class="h-40 w-full" />
          <ModelAnalizi v-else-if="analiz" :rapor="analiz" :tedarikciler="tedarikciler" />
          <UCard v-else variant="subtle">
            <p class="flex items-center gap-2 text-sm text-muted">
              <UIcon name="i-lucide-bot" class="size-4" />
              Model bu haber için henüz çıkarım raporu göndermedi.
            </p>
          </UCard>
        </section>
      </div>
    </div>

    <UModal
      v-model:open="silinecek"
      title="Olayı kaldır"
      :description="secili ? `“${secili.baslik}” ve modelin çıkarımı kalıcı olarak kaldırılacak. Model aynı olayı yeniden gönderebilir.` : ''"
    >
      <template #footer>
        <div class="flex justify-end gap-2 w-full">
          <UButton label="Vazgeç" color="neutral" variant="ghost" @click="silinecek = false" />
          <UButton label="Kaldır" color="error" @click="olayiSil" />
        </div>
      </template>
    </UModal>
  </SayfaPaneli>
</template>
