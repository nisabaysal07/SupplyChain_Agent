<script setup lang="ts">
const toast = useToast()
const { fetch: oturumuYenile } = useUserSession()

const [{ data: profil, refresh: profiliYenile }, { data: sistem }] = await Promise.all([
  useFetch<Kullanici>('/api/profil'),
  useFetch<SistemDurumu>('/api/sistem')
])

const yonetici = computed(() => profil.value?.rol === 'yonetici')

// Formlar sunucudaki değerin kopyasıyla çalışır; "Vazgeç" kopyayı sıfırlar
const profilFormu = reactive({ ad: '', soyad: '' })
const bildirimFormu = reactive<BildirimTercihleri>({ eposta: true, uygulamaIci: true, seviyeler: [] })
const sistemFormu = reactive<SistemAyarlari>({ senkronizasyonSaat: 12 })

function formlariDoldur() {
  if (profil.value) {
    Object.assign(profilFormu, { ad: profil.value.ad, soyad: profil.value.soyad })
    Object.assign(bildirimFormu, { ...profil.value.bildirimler, seviyeler: [...profil.value.bildirimler.seviyeler] })
  }
  if (sistem.value) sistemFormu.senkronizasyonSaat = sistem.value.senkronizasyonSaat
}
watch([profil, sistem], formlariDoldur, { immediate: true })

const profilDegisti = computed(() =>
  profil.value && (profilFormu.ad !== profil.value.ad || profilFormu.soyad !== profil.value.soyad))
const bildirimDegisti = computed(() =>
  profil.value && JSON.stringify(bildirimFormu) !== JSON.stringify(profil.value.bildirimler))
const sistemDegisti = computed(() =>
  sistem.value && sistemFormu.senkronizasyonSaat !== sistem.value.senkronizasyonSaat)

const kaydediliyor = ref<'profil' | 'bildirim' | 'sistem' | null>(null)

async function kaydet(ne: 'profil' | 'bildirim' | 'sistem') {
  kaydediliyor.value = ne
  try {
    if (ne === 'profil') {
      await $fetch('/api/profil', { method: 'PATCH', body: profilFormu })
      await oturumuYenile()
    }
    else if (ne === 'bildirim') {
      await $fetch('/api/profil/bildirimler', { method: 'PATCH', body: bildirimFormu })
    }
    else {
      sistem.value = { ...sistem.value!, ...await $fetch<SistemAyarlari>('/api/sistem', { method: 'PATCH', body: sistemFormu }) }
    }
    if (ne !== 'sistem') await profiliYenile()
    toast.add({ title: 'Değişiklikler kaydedildi', color: 'success', icon: 'i-lucide-check' })
  }
  catch {
    toast.add({ title: 'Kaydedilemedi', description: 'Lütfen alanları kontrol edip tekrar deneyin.', color: 'error', icon: 'i-lucide-circle-alert' })
  }
  finally {
    kaydediliyor.value = null
  }
}

const sifreAcik = ref(false)

const seviyeSecenekleri = (['yuksek', 'orta', 'dusuk'] as const).map(s => ({ value: s, label: SEVIYE_ETIKETI[s] }))
const siklikSecenekleri = [
  { value: 6, label: '6 saatte bir' },
  { value: 12, label: '12 saatte bir' },
  { value: 24, label: 'Günde bir' }
]
const veriKaynagi = computed(() => {
  const k = sistem.value?.veriKaynagi
  if (k?.tur !== 'postgresql') {
    return { ad: 'CSV dosyaları', degisken: 'NUXT_DATABASE_URL tanımlı değil', durum: 'Kullanımda', renk: 'neutral' as const, icon: 'i-lucide-file-text' }
  }
  return k.durum === 'bagli'
    ? { ad: 'PostgreSQL', degisken: 'NUXT_DATABASE_URL', durum: 'Bağlı', renk: 'success' as const, icon: 'i-lucide-database' }
    : { ad: 'PostgreSQL', degisken: 'NUXT_DATABASE_URL', durum: 'Bağlanamadı', renk: 'error' as const, icon: 'i-lucide-circle-alert' }
})

const anahtarlar = computed(() => [
  { ad: 'Tavily (haber arama)', tanimli: sistem.value?.anahtarlar.tavily, degisken: 'NUXT_TAVILY_API_KEY' },
  { ad: 'Nemotron (yapay zekâ analizi)', tanimli: sistem.value?.anahtarlar.nemotron, degisken: 'NUXT_NEMOTRON_API_KEY' }
])
</script>

<template>
  <SayfaPaneli baslik="Ayarlar">
    <div v-if="profil" class="grid gap-6 lg:grid-cols-2 2xl:grid-cols-3 items-start">
      <!-- Profil -->
      <UCard>
        <template #header>
          <h2 class="font-semibold text-highlighted">Profil</h2>
        </template>

        <div class="flex items-center gap-3 mb-5">
          <UAvatar :alt="`${profil.ad} ${profil.soyad}`" size="lg" />
          <div class="min-w-0">
            <p class="font-medium text-highlighted truncate">{{ profil.ad }} {{ profil.soyad }}</p>
            <p class="text-sm text-muted truncate">{{ profil.eposta }}</p>
          </div>
          <UBadge :label="yonetici ? 'Yönetici' : 'İzleyici'" color="neutral" variant="subtle" class="ms-auto" />
        </div>

        <UForm :schema="ProfilSemasi" :state="profilFormu" class="space-y-4" @submit="kaydet('profil')">
          <div class="grid gap-4 sm:grid-cols-2">
            <UFormField label="Ad" name="ad">
              <UInput v-model="profilFormu.ad" autocomplete="given-name" class="w-full" />
            </UFormField>
            <UFormField label="Soyad" name="soyad">
              <UInput v-model="profilFormu.soyad" autocomplete="family-name" class="w-full" />
            </UFormField>
          </div>
          <UFormField label="E-posta" help="E-posta adresi yönetici tarafından değiştirilir.">
            <UInput :model-value="profil.eposta" disabled class="w-full" />
          </UFormField>

          <div class="flex flex-wrap gap-2 pt-1">
            <UButton type="submit" label="Kaydet" :disabled="!profilDegisti" :loading="kaydediliyor === 'profil'" />
            <UButton label="Vazgeç" color="neutral" variant="ghost" :disabled="!profilDegisti" @click="formlariDoldur" />
            <UButton
              label="Şifre değiştir"
              icon="i-lucide-key-round"
              color="neutral"
              variant="outline"
              class="ms-auto"
              @click="sifreAcik = true"
            />
          </div>
        </UForm>
      </UCard>

      <!-- Bildirimler -->
      <UCard>
        <template #header>
          <h2 class="font-semibold text-highlighted">Bildirim tercihleri</h2>
        </template>

        <div class="space-y-5">
          <USwitch
            v-model="bildirimFormu.eposta"
            label="E-posta bildirimleri"
            description="Seçili seviyedeki yeni olaylar e-posta ile bildirilir."
          />
          <USwitch
            v-model="bildirimFormu.uygulamaIci"
            label="Uygulama içi bildirimler"
            description="Yeni olaylar panelde bildirim olarak görünür."
          />
          <UFormField label="Hangi şiddetteki olaylar bildirilsin?">
            <UCheckboxGroup v-model="bildirimFormu.seviyeler" :items="seviyeSecenekleri" orientation="horizontal" class="mt-1" />
          </UFormField>

          <UAlert
            color="neutral"
            variant="subtle"
            icon="i-lucide-info"
            description="Uygulama içi bildirimler sağ üstteki zilde görünür. Seviye, modelin çıkarımı varsa onun genel değerlendirmesine, yoksa haberin şiddetine göredir. E-posta gönderimi henüz bağlı değil."
          />

          <div class="flex gap-2">
            <UButton label="Kaydet" :disabled="!bildirimDegisti" :loading="kaydediliyor === 'bildirim'" @click="kaydet('bildirim')" />
            <UButton label="Vazgeç" color="neutral" variant="ghost" :disabled="!bildirimDegisti" @click="formlariDoldur" />
          </div>
        </div>
      </UCard>

      <!-- Sistem -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="font-semibold text-highlighted">Sistem</h2>
            <UBadge v-if="!yonetici" label="Yalnızca görüntüleme" color="neutral" variant="outline" size="sm" />
          </div>
        </template>

        <div class="space-y-5">
          <div>
            <p class="text-sm font-medium text-highlighted">Veri kaynağı</p>
            <div class="mt-2 flex items-center justify-between gap-3 rounded-md border border-default px-3 py-2.5">
              <div class="min-w-0">
                <p class="text-sm text-highlighted">{{ veriKaynagi.ad }}</p>
                <p class="text-xs text-muted font-mono truncate">{{ veriKaynagi.degisken }}</p>
              </div>
              <UBadge :label="veriKaynagi.durum" :color="veriKaynagi.renk" :icon="veriKaynagi.icon" variant="subtle" />
            </div>
          </div>

          <div>
            <p class="text-sm font-medium text-highlighted">API anahtarları</p>
            <ul class="mt-2 divide-y divide-default rounded-md border border-default">
              <li v-for="a in anahtarlar" :key="a.degisken" class="flex items-center justify-between gap-3 px-3 py-2.5">
                <div class="min-w-0">
                  <p class="text-sm text-highlighted">{{ a.ad }}</p>
                  <p class="text-xs text-muted font-mono truncate">{{ a.degisken }}</p>
                </div>
                <UBadge
                  :label="a.tanimli ? 'Tanımlı' : 'Tanımlı değil'"
                  :color="a.tanimli ? 'success' : 'warning'"
                  :icon="a.tanimli ? 'i-lucide-check' : 'i-lucide-circle-alert'"
                  variant="subtle"
                />
              </li>
            </ul>
            <p class="mt-2 text-xs text-muted">
              Güvenlik için anahtarlar bu ekranda gösterilmez ve buradan değiştirilmez;
              sunucudaki <span class="font-mono">.env</span> dosyasından yönetilir.
            </p>
          </div>

          <UFormField label="Veri senkronizasyon sıklığı" help="Canlı olay kaynakları bu aralıkla taranacak.">
            <USelect
              v-model="sistemFormu.senkronizasyonSaat"
              :items="siklikSecenekleri"
              :disabled="!yonetici"
              class="w-full"
            />
          </UFormField>

          <div v-if="yonetici" class="flex gap-2">
            <UButton label="Kaydet" :disabled="!sistemDegisti" :loading="kaydediliyor === 'sistem'" @click="kaydet('sistem')" />
            <UButton label="Vazgeç" color="neutral" variant="ghost" :disabled="!sistemDegisti" @click="formlariDoldur" />
          </div>
        </div>
      </UCard>
    </div>

    <SifreDegistir v-model:open="sifreAcik" />
  </SayfaPaneli>
</template>
