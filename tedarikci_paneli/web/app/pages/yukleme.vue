<script setup lang="ts">
// Şirketin company_file Excel'ini supply_db'ye aktarır (server/api/yukleme.post.ts). Yalnızca yönetici.
const { user } = useUserSession()
const yonetici = computed(() => user.value?.rol === 'yonetici')
const { t, sayi, ondalik, saat } = useDil()

type Tablo = 'items' | 'suppliers' | 'supplier_items' | 'contracts' | 'shipments' | 'inventory'
interface YuklemeRaporu {
  totalRows: number
  importedRows: number
  inserted: Record<Tablo, number>
  alreadyExisted: Record<Tablo, number>
  errors: { row: number, message: string }[]
}

// Sunucudaki sınırla aynı (yukleme.post.ts → EN_BUYUK_BOYUT)
const EN_BUYUK_BOYUT = 5 * 1024 * 1024

/*
 * Excel sütunlarının hangi tabloya yazıldığı (server/utils/importer.ts → importOne).
 * zorunlu: her satırda dolu olmalı · bos: başlık olmalı, hücre boş kalabilir · yeniUrun: yalnızca yeni ürün eklerken
 */
type SutunTuru = 'zorunlu' | 'bos' | 'yeniUrun'
// Tablo adları arayüz dilinde: t(`yuk.tablolar.${tablo}`)
const TABLOLAR: { tablo: Tablo, sutunlar: [string, SutunTuru][] }[] = [
  { tablo: 'suppliers', sutunlar: [['name', 'zorunlu'], ['country', 'zorunlu'], ['name_original', 'bos']] },
  { tablo: 'items', sutunlar: [['item', 'zorunlu'], ['hs6', 'yeniUrun'], ['gtip', 'yeniUrun'], ['unit', 'yeniUrun']] },
  { tablo: 'supplier_items', sutunlar: [['item_model', 'zorunlu'], ['assembly_country', 'zorunlu'], ['annual_quantity', 'bos']] },
  {
    tablo: 'contracts',
    sutunlar: [['contract_start_date', 'zorunlu'], ['currency', 'zorunlu'], ['unit_price', 'zorunlu'], ['contract_end_date', 'bos'], ['purchase_amount', 'bos'], ['price_date', 'bos']]
  },
  {
    tablo: 'shipments',
    sutunlar: [['transport_mode', 'zorunlu'], ['exit_location', 'zorunlu'], ['destination_location', 'zorunlu'], ['shipments_status', 'bos'], ['expected_transit_days', 'bos']]
  },
  { tablo: 'inventory', sutunlar: [['item_on_hand', 'bos'], ['item_reserved', 'bos'], ['reorder_point', 'bos']] }
]

const dosya = ref<File | null>(null)
const surukleniyor = ref(false)
const secimHatasi = ref('')
const yukleniyor = ref(false)
const hata = ref('')
const eksikSutunlar = ref<string[]>([])
const rapor = ref<YuklemeRaporu | null>(null)
const raporZamani = ref('')
const raporDosyasi = ref('')
const tumHatalar = ref(false)
const girdi = ref<HTMLInputElement | null>(null)

const boyutBicimi = (b: number) => b < 1024 * 1024 ? `${sayi(Math.max(1, Math.round(b / 1024)))} KB` : `${ondalik(b / 1024 / 1024)} MB`

function sec(f: File | undefined) {
  secimHatasi.value = ''
  if (!f) return
  if (!f.name.toLowerCase().endsWith('.xlsx')) {
    secimHatasi.value = t('yuk.xlsxDegil', { ad: f.name })
    return
  }
  if (f.size > EN_BUYUK_BOYUT) {
    secimHatasi.value = t('yuk.cokBuyuk', { ad: f.name, boyut: boyutBicimi(f.size) })
    return
  }
  dosya.value = f
  hata.value = ''
  eksikSutunlar.value = []
}

function girdidenSec(e: Event) {
  const el = e.target as HTMLInputElement
  sec(el.files?.[0])
  el.value = '' // aynı dosya yeniden seçilebilsin
}

function birak(e: DragEvent) {
  surukleniyor.value = false
  sec(e.dataTransfer?.files?.[0])
}

function kaldir() {
  dosya.value = null
  secimHatasi.value = ''
}

const toast = useToast()
async function yukle() {
  if (!dosya.value || yukleniyor.value) return
  yukleniyor.value = true
  hata.value = ''
  eksikSutunlar.value = []
  rapor.value = null
  tumHatalar.value = false
  const form = new FormData()
  form.append('file', dosya.value)
  try {
    rapor.value = await $fetch<YuklemeRaporu>('/api/yukleme', { method: 'POST', body: form })
    raporZamani.value = saat(new Date())
    raporDosyasi.value = dosya.value.name
    dosya.value = null
    toast.add({ title: t('yuk.aktarildi'), color: 'success', icon: 'i-lucide-check' })
  }
  catch (e) {
    const err = e as { data?: { data?: { message?: string }, message?: string }, statusMessage?: string }
    // Durum metni (statusMessage) Türkçe karakterleri bozar; gövdedeki mesaj önce okunur.
    // Sunucunun Excel doğrulama mesajları Türkçedir (server/utils/excel.ts, importer.ts)
    hata.value = err.data?.data?.message ?? err.data?.message ?? err.statusMessage ?? t('yuk.hataGenel')
    // excel.ts: "Excel'de eksik kolon(lar): a, b" → sağdaki sütun listesinde işaretlenir
    const eslesme = hata.value.match(/eksik kolon\(lar\):\s*(.+)$/)
    if (eslesme) eksikSutunlar.value = eslesme[1]!.split(',').map(s => s.trim())
  }
  finally {
    yukleniyor.value = false
  }
}

// Sonuç çubukları tek ölçekte: en çok kayıt gören tablo tam genişlik
const satirlar = computed(() => {
  const r = rapor.value
  if (!r) return TABLOLAR.map(t => ({ ...t, yeni: 0, vardi: 0, yeniPay: 0, vardiPay: 0 }))
  const enCok = Math.max(1, ...TABLOLAR.map(t => r.inserted[t.tablo] + r.alreadyExisted[t.tablo]))
  return TABLOLAR.map(t => ({
    ...t,
    yeni: r.inserted[t.tablo],
    vardi: r.alreadyExisted[t.tablo],
    yeniPay: r.inserted[t.tablo] / enCok * 100,
    vardiPay: r.alreadyExisted[t.tablo] / enCok * 100
  }))
})
const gorunenHatalar = computed(() => {
  const h = rapor.value?.errors ?? []
  return tumHatalar.value ? h : h.slice(0, 6)
})
</script>

<template>
  <SayfaPaneli :baslik="t('nav.yukleme')">
    <UAlert
      v-if="!yonetici"
      color="warning"
      variant="subtle"
      icon="i-lucide-lock"
      :title="t('yuk.yetkiGerekli')"
      :description="t('yuk.yetkiAcik')"
    />

    <!-- Izgara: sol sütun esnek, sağ sütun 360px, 24px aralık; iki sütun da tuvalin kenarlarına oturur -->
    <div v-else class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-start">
      <!-- Aktarımdan sonra sonuç (ya da hata) yükleme alanının üstüne çıkar: ekranın sorusu artık "ne eklendi?" -->
      <div class="flex min-w-0 flex-col gap-6">
        <!-- Yükleme -->
        <section aria-labelledby="yukle-baslik" class="rounded-lg border border-default bg-default p-5 sm:p-6">
          <h2 id="yukle-baslik" class="text-base font-semibold text-highlighted">{{ t('yuk.excelBaslik') }}</h2>
          <p class="mt-1 max-w-prose text-sm text-muted">
            {{ t('yuk.excelAcik', { sayfa: 'company_file' }) }}
          </p>

          <form class="mt-5" @submit.prevent="yukle">
            <!-- Dosya seçilmediyse bırakma alanı, seçildiyse dosya satırı -->
            <label
              v-if="!dosya"
              class="flex min-h-36 cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border border-dashed px-4 py-6 text-center transition-colors duration-150 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-primary"
              :class="surukleniyor ? 'border-primary bg-primary/5' : 'border-accented hover:bg-muted'"
              @dragenter.prevent="surukleniyor = true"
              @dragover.prevent="surukleniyor = true"
              @dragleave.prevent="surukleniyor = false"
              @drop.prevent="birak"
            >
              <UIcon name="i-lucide-file-spreadsheet" class="mb-1 size-5 text-dimmed" />
              <span class="text-sm font-medium text-highlighted">
                {{ t('yuk.birak') }} <span class="text-primary underline underline-offset-2">{{ t('yuk.sec') }}</span>
              </span>
              <span id="dosya-kurali" class="text-sm text-muted">{{ t('yuk.kural') }}</span>
              <input
                ref="girdi"
                type="file"
                accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                class="sr-only"
                aria-describedby="dosya-kurali dosya-hatasi"
                @change="girdidenSec"
              >
            </label>

            <div v-else class="flex items-center gap-3 rounded-lg bg-muted px-4 py-3">
              <UIcon name="i-lucide-file-spreadsheet" class="size-5 shrink-0 text-toned" />
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-medium text-highlighted">{{ dosya.name }}</p>
                <p class="text-xs text-muted tabular-nums">{{ boyutBicimi(dosya.size) }}</p>
              </div>
              <UButton :label="t('genel.kaldir')" color="neutral" variant="ghost" size="sm" :disabled="yukleniyor" @click="kaldir" />
            </div>

            <p id="dosya-hatasi" class="text-sm text-error" :class="secimHatasi && 'mt-2'" aria-live="polite">{{ secimHatasi }}</p>

            <div class="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2">
              <UButton type="submit" icon="i-lucide-database" :loading="yukleniyor" :disabled="!dosya">
                {{ t(yukleniyor ? 'yuk.aktariliyor' : 'yuk.aktar') }}
              </UButton>
              <span v-if="!dosya" class="text-sm text-muted">{{ t('yuk.onceSec') }}</span>
            </div>
          </form>
        </section>

        <!-- Aktarılıyor -->
        <section v-if="yukleniyor" aria-live="polite" class="rounded-lg border border-default bg-default p-5 sm:p-6">
          <h2 class="text-base font-semibold text-highlighted">{{ t('yuk.sonuc') }}</h2>
          <p class="mt-1 text-sm text-muted">{{ t('yuk.okunuyor') }}</p>
        </section>

        <!-- Hata: başarısız olan bloğun içinde -->
        <section v-else-if="hata" role="alert" class="order-first rounded-lg border border-default bg-default p-5 sm:p-6">
          <h2 class="flex items-center gap-2 text-base font-semibold text-highlighted">
            <UIcon name="i-lucide-circle-x" class="size-4 text-error" />
            {{ t('yuk.aktarilamadi') }}
          </h2>
          <p class="mt-1 text-sm text-toned">{{ hata }}</p>
          <p class="mt-2 text-sm text-muted">
            <template v-if="eksikSutunlar.length">{{ t('yuk.eksikSutun', { n: eksikSutunlar.length }) }}</template>
            <template v-else>{{ t('yuk.hicYazilmadi') }}</template>
          </p>
        </section>

        <!-- Sonuç: aktarımdan önce de çerçevesi ve tabloları durur, sayılar yerine çizgi -->
        <section v-else aria-labelledby="sonuc-baslik" :class="rapor && 'order-first'" class="rounded-lg border border-default bg-default p-5 sm:p-6">
          <div class="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
            <h2 id="sonuc-baslik" class="text-base font-semibold text-highlighted">{{ t('yuk.sonuc') }}</h2>
            <p v-if="rapor" class="min-w-0 truncate text-sm text-muted">{{ raporDosyasi }} · {{ raporZamani }}</p>
          </div>

          <p v-if="!rapor" class="mt-1 text-sm text-muted">{{ t('yuk.henuzYok') }}</p>

          <p v-else class="mt-3 flex flex-wrap items-baseline gap-x-2">
            <span class="text-3xl font-semibold tracking-tight text-highlighted tabular-nums">{{ sayi(rapor.importedRows) }}</span>
            <span class="text-base text-muted tabular-nums">{{ t('yuk.satirAktarildi', { n: sayi(rapor.totalRows) }) }}</span>
          </p>
          <p v-if="rapor" class="mt-1 text-sm text-muted">
            <template v-if="rapor.errors.length">
              <span class="font-medium text-error tabular-nums">{{ t('yuk.hataliSatir', { n: rapor.errors.length }) }}</span>
              {{ t('yuk.hataliSatirAcik') }}
            </template>
            <template v-else>{{ t('yuk.tumAktarildi') }}</template>
          </p>

          <table class="mt-6 w-full text-sm">
            <caption class="sr-only">{{ t('yuk.tabloAciklama') }}</caption>
            <thead>
              <tr class="text-xs text-muted">
                <th scope="col" class="pb-2 text-left font-normal">{{ t('yuk.tablo') }}</th>
                <th scope="col" class="pb-2 pl-4 text-right font-normal whitespace-nowrap">
                  <span class="mr-1.5 inline-block size-2 rounded-[2px] bg-primary align-middle" aria-hidden="true" />{{ t('yuk.yeniEklenen') }}
                </th>
                <th scope="col" class="pb-2 pl-4 text-right font-normal whitespace-nowrap">
                  <span class="mr-1.5 inline-block size-2 rounded-[2px] bg-accented align-middle" aria-hidden="true" />{{ t('yuk.zatenVardi') }}
                </th>
                <th scope="col" class="hidden w-[32%] pb-2 pl-6 sm:table-cell"><span class="sr-only">{{ t('yuk.oran') }}</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in satirlar" :key="s.tablo" class="border-t border-muted">
                <th scope="row" class="py-2.5 text-left font-normal">
                  <span class="text-highlighted">{{ t(`yuk.tablolar.${s.tablo}`) }}</span>
                  <code class="ml-2 hidden text-xs text-muted md:inline">{{ s.tablo }}</code>
                </th>
                <td class="py-2.5 pl-4 text-right tabular-nums" :class="s.yeni ? 'font-medium text-primary' : 'text-muted'">
                  {{ rapor ? sayi(s.yeni) : '—' }}
                </td>
                <td class="py-2.5 pl-4 text-right tabular-nums" :class="s.vardi ? 'text-toned' : 'text-muted'">
                  {{ rapor ? sayi(s.vardi) : '—' }}
                </td>
                <td class="hidden py-2.5 pl-6 sm:table-cell" aria-hidden="true">
                  <div v-if="rapor" class="flex h-2 gap-0.5">
                    <div v-if="s.yeni" class="rounded-[2px] bg-primary" :style="{ width: `${s.yeniPay}%` }" />
                    <div v-if="s.vardi" class="rounded-[2px] bg-accented" :style="{ width: `${s.vardiPay}%` }" />
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <div v-if="rapor?.errors.length" class="mt-8">
            <h3 class="text-sm font-semibold text-highlighted">
              {{ t('yuk.aktarilamayan') }} <span class="font-normal text-muted tabular-nums">({{ sayi(rapor.errors.length) }})</span>
            </h3>
            <table class="mt-2 w-full text-sm">
              <caption class="sr-only">{{ t('yuk.hataAciklama') }}</caption>
              <thead>
                <tr class="text-xs text-muted">
                  <th scope="col" class="w-16 pb-2 text-right font-normal">{{ t('yuk.satir') }}</th>
                  <th scope="col" class="pb-2 pl-4 text-left font-normal">{{ t('yuk.neden') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="e in gorunenHatalar" :key="e.row" class="border-t border-muted align-top">
                  <td class="py-2 text-right text-highlighted tabular-nums">{{ e.row }}</td>
                  <td class="py-2 pl-4 text-toned">{{ e.message }}</td>
                </tr>
              </tbody>
            </table>
            <UButton
              v-if="rapor.errors.length > 6"
              class="mt-2 px-0"
              color="neutral"
              variant="link"
              size="sm"
              :label="tumHatalar ? t('yuk.dahaAz') : t('yuk.tumunuGoster', { n: rapor.errors.length })"
              @click="tumHatalar = !tumHatalar"
            />
          </div>
        </section>
      </div>

      <!-- Beklenen sütunlar: hangi Excel başlığı hangi tabloya yazılır -->
      <aside aria-labelledby="sutun-baslik" class="rounded-lg bg-muted p-5">
        <h2 id="sutun-baslik" class="text-base font-semibold text-highlighted">{{ t('yuk.beklenen') }}</h2>
        <p class="mt-1 text-sm text-muted">{{ t('yuk.beklenenAcik') }}</p>

        <ul class="mt-4 flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-muted">
          <li class="flex items-center gap-1.5"><span class="sutun sutun--zorunlu">abc</span> {{ t('yuk.zorunlu') }}</li>
          <li class="flex items-center gap-1.5"><span class="sutun sutun--bos">abc</span> {{ t('yuk.bos') }}</li>
          <li class="flex items-center gap-1.5"><span class="sutun sutun--yeniUrun">abc</span> {{ t('yuk.yeniUrun') }}</li>
        </ul>

        <div v-for="tb in TABLOLAR" :key="tb.tablo" class="mt-5">
          <h3 class="flex items-baseline justify-between gap-2 text-sm">
            <span class="font-medium text-highlighted">{{ t(`yuk.tablolar.${tb.tablo}`) }}</span>
            <code class="text-xs text-muted">{{ tb.tablo }}</code>
          </h3>
          <ul class="mt-2 flex flex-wrap gap-1.5">
            <li
              v-for="[ad, tur] in tb.sutunlar"
              :key="ad"
              class="sutun"
              :class="eksikSutunlar.includes(ad) ? 'sutun--eksik' : `sutun--${tur}`"
            >
              {{ ad }}<span v-if="eksikSutunlar.includes(ad)" class="ml-1 font-sans font-medium">· {{ t('yuk.eksik') }}</span>
            </li>
          </ul>
        </div>
      </aside>
    </div>
  </SayfaPaneli>
</template>

<style scoped>
/* Excel başlık adları kod olduğu için eşaralıklı; tür, dolgu ve yazı tonuyla ayrışır */
.sutun {
  display: inline-flex;
  flex: none;
  align-items: center;
  white-space: nowrap;
  border: 1px solid transparent;
  border-radius: 4px;
  padding: 0.0625rem 0.3125rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; /* taste-skill-ignore: Excel başlıkları birebir koddur */
  font-size: 0.75rem;
  line-height: 1.25rem;
}
.sutun--zorunlu { background: var(--ui-bg-accented); color: var(--ui-text-highlighted); }
.sutun--bos { background: var(--ui-bg); color: var(--ui-text-toned); border-color: var(--ui-border-accented); }
.sutun--yeniUrun { color: var(--ui-text-muted); padding-inline: 0.0625rem; }
.sutun--eksik { background: var(--ui-color-error-50); color: var(--ui-color-error-800); border-color: var(--ui-color-error-200); }
</style>
