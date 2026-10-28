<script setup lang="ts">
const toast = useToast()
const { t, tarihSaat } = useDil()
const { fetch: oturumuYenile } = useUserSession()

const [{ data: profil, refresh: profiliYenile }, { data: sistem }] = await Promise.all([
  useFetch<Kullanici>('/api/profil'),
  useFetch<SistemDurumu>('/api/sistem')
])

const yonetici = computed(() => profil.value?.rol === 'yonetici')

// Formlar sunucudaki değerin kopyasıyla çalışır; "Vazgeç" kopyayı sıfırlar
const profilFormu = reactive({ ad: '', soyad: '' })
const bildirimFormu = reactive<BildirimTercihleri>({ eposta: true, uygulamaIci: true, seviyeler: [] })
const sistemFormu = reactive<SistemAyarlari>({ senkronizasyonSaat: 3 })

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
    toast.add({ title: t('ayar.kaydedildi'), color: 'success', icon: 'i-lucide-check' })
  }
  catch {
    toast.add({ title: t('ayar.kaydedilemedi'), description: t('ayar.kaydedilemediAcik'), color: 'error', icon: 'i-lucide-circle-alert' })
  }
  finally {
    kaydediliyor.value = null
  }
}

const sifreAcik = ref(false)

const seviyeSecenekleri = computed(() => (['yuksek', 'orta', 'dusuk'] as const).map(s => ({ value: s, label: t(`seviye.${s}`) })))
const siklikSecenekleri = computed(() => ([1, 3, 6, 12, 24] as const).map(saat => ({
  value: saat,
  label: saat === 24 ? t('ayar.siklikGunde') : t('ayar.siklikSaat', { n: saat })
})))
const sonTarama = computed(() => {
  const s = sistem.value?.sonTarama
  if (!s) return t('ayar.sonTaramaYok')
  return t('ayar.sonTarama', { zaman: tarihSaat(s.baslangic), durum: t(`ayar.taramaDurumu.${s.durum}`) })
})
const veriKaynagi = computed(() => {
  const k = sistem.value?.veriKaynagi
  if (k?.tur !== 'postgresql') {
    return { ad: 'PostgreSQL', degisken: t('ayar.postgresTanimsiz'), durum: t('ayar.bagliDegil'), renk: 'neutral' as const, icon: 'i-lucide-database' }
  }
  return k.durum === 'bagli'
    ? { ad: 'PostgreSQL', degisken: 'POSTGRES_* (.env)', durum: t('ayar.bagli'), renk: 'success' as const, icon: 'i-lucide-database' }
    : { ad: 'PostgreSQL', degisken: 'POSTGRES_* (.env)', durum: t('ayar.baglanamadi'), renk: 'error' as const, icon: 'i-lucide-circle-alert' }
})

const anahtarlar = computed(() => [
  { ad: t('ayar.tavily'), tanimli: sistem.value?.anahtarlar.tavily, degisken: 'TAVILY_API_KEY' },
  { ad: t('ayar.nebius'), tanimli: sistem.value?.anahtarlar.nebius, degisken: 'NEBIUS_API_KEY' },
  { ad: t('ayar.modelErisimi'), tanimli: sistem.value?.anahtarlar.modelErisimi, degisken: 'NUXT_MODEL_API_TOKEN' },
  { ad: t('ayar.bildirimKanallari'), tanimli: sistem.value?.anahtarlar.bildirimKanallari, degisken: 'NOTIFY_URLS' }
])
</script>

<template>
  <SayfaPaneli :baslik="t('nav.ayarlar')">
    <div v-if="profil" class="grid gap-6 lg:grid-cols-2 2xl:grid-cols-3 items-start">
      <!-- Profil -->
      <UCard>
        <template #header>
          <h2 class="font-semibold text-highlighted">{{ t('ayar.profil') }}</h2>
        </template>

        <div class="flex items-center gap-3 mb-5">
          <UAvatar :alt="`${profil.ad} ${profil.soyad}`" size="lg" />
          <div class="min-w-0">
            <p class="font-medium text-highlighted truncate">{{ profil.ad }} {{ profil.soyad }}</p>
            <p class="text-sm text-muted truncate">{{ profil.eposta }}</p>
          </div>
          <UBadge :label="t(yonetici ? 'rol.yonetici' : 'rol.izleyici')" color="neutral" variant="subtle" class="ms-auto" />
        </div>

        <UForm :schema="ProfilSemasi" :state="profilFormu" class="space-y-4" @submit="kaydet('profil')">
          <div class="grid gap-4 sm:grid-cols-2">
            <UFormField :label="t('ayar.ad')" name="ad">
              <UInput v-model="profilFormu.ad" autocomplete="given-name" class="w-full" />
              <template #error="{ error }">{{ typeof error === 'string' ? t(error) : '' }}</template>
            </UFormField>
            <UFormField :label="t('ayar.soyad')" name="soyad">
              <UInput v-model="profilFormu.soyad" autocomplete="family-name" class="w-full" />
              <template #error="{ error }">{{ typeof error === 'string' ? t(error) : '' }}</template>
            </UFormField>
          </div>
          <UFormField :label="t('ayar.eposta')" :help="t('ayar.epostaYardim')">
            <UInput :model-value="profil.eposta" disabled class="w-full" />
          </UFormField>

          <div class="flex flex-wrap gap-2 pt-1">
            <UButton type="submit" :label="t('genel.kaydet')" :disabled="!profilDegisti" :loading="kaydediliyor === 'profil'" />
            <UButton :label="t('genel.vazgec')" color="neutral" variant="ghost" :disabled="!profilDegisti" @click="formlariDoldur" />
            <UButton
              :label="t('sifre.baslik')"
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
          <h2 class="font-semibold text-highlighted">{{ t('ayar.bildirimTercihleri') }}</h2>
        </template>

        <div class="space-y-5">
          <USwitch
            v-model="bildirimFormu.eposta"
            :label="t('ayar.epostaBildirim')"
            :description="t('ayar.epostaBildirimAcik')"
          />
          <USwitch
            v-model="bildirimFormu.uygulamaIci"
            :label="t('ayar.uygulamaIci')"
            :description="t('ayar.uygulamaIciAcik')"
          />
          <UFormField :label="t('ayar.hangiSiddet')">
            <UCheckboxGroup v-model="bildirimFormu.seviyeler" :items="seviyeSecenekleri" orientation="horizontal" class="mt-1" />
          </UFormField>

          <UAlert
            color="neutral"
            variant="subtle"
            icon="i-lucide-info"
            :description="t('ayar.bildirimBilgi')"
          />

          <div class="flex gap-2">
            <UButton :label="t('genel.kaydet')" :disabled="!bildirimDegisti" :loading="kaydediliyor === 'bildirim'" @click="kaydet('bildirim')" />
            <UButton :label="t('genel.vazgec')" color="neutral" variant="ghost" :disabled="!bildirimDegisti" @click="formlariDoldur" />
          </div>
        </div>
      </UCard>

      <!-- Sistem -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="font-semibold text-highlighted">{{ t('ayar.sistem') }}</h2>
            <UBadge v-if="!yonetici" :label="t('ayar.yalnizcaGoruntuleme')" color="neutral" variant="outline" size="sm" />
          </div>
        </template>

        <div class="space-y-5">
          <div>
            <p class="text-sm font-medium text-highlighted">{{ t('ayar.veriKaynagi') }}</p>
            <div class="mt-2 flex items-center justify-between gap-3 rounded-md border border-default px-3 py-2.5">
              <div class="min-w-0">
                <p class="text-sm text-highlighted">{{ veriKaynagi.ad }}</p>
                <p class="text-xs text-muted font-mono truncate">{{ veriKaynagi.degisken }}</p>
              </div>
              <UBadge :label="veriKaynagi.durum" :color="veriKaynagi.renk" :icon="veriKaynagi.icon" variant="subtle" />
            </div>
          </div>

          <div>
            <p class="text-sm font-medium text-highlighted">{{ t('ayar.apiAnahtarlari') }}</p>
            <ul class="mt-2 divide-y divide-default rounded-md border border-default">
              <li v-for="a in anahtarlar" :key="a.degisken" class="flex items-center justify-between gap-3 px-3 py-2.5">
                <div class="min-w-0">
                  <p class="text-sm text-highlighted">{{ a.ad }}</p>
                  <p class="text-xs text-muted font-mono truncate">{{ a.degisken }}</p>
                </div>
                <UBadge
                  :label="t(a.tanimli ? 'ayar.tanimli' : 'ayar.tanimliDegil')"
                  :color="a.tanimli ? 'success' : 'warning'"
                  :icon="a.tanimli ? 'i-lucide-check' : 'i-lucide-circle-alert'"
                  variant="subtle"
                />
              </li>
            </ul>
            <p class="mt-2 text-xs text-muted">
              {{ t('ayar.anahtarNotu', { dosya: '.env' }) }}
            </p>
          </div>

          <UFormField :label="t('ayar.senkron')" :help="`${t('ayar.senkronYardim')} ${sonTarama}`">
            <USelect
              v-model="sistemFormu.senkronizasyonSaat"
              :items="siklikSecenekleri"
              :disabled="!yonetici"
              class="w-full"
            />
          </UFormField>

          <div v-if="yonetici" class="flex gap-2">
            <UButton :label="t('genel.kaydet')" :disabled="!sistemDegisti" :loading="kaydediliyor === 'sistem'" @click="kaydet('sistem')" />
            <UButton :label="t('genel.vazgec')" color="neutral" variant="ghost" :disabled="!sistemDegisti" @click="formlariDoldur" />
          </div>
        </div>
      </UCard>
    </div>

    <SifreDegistir v-model:open="sifreAcik" />
  </SayfaPaneli>
</template>
