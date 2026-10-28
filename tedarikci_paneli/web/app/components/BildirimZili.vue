<script setup lang="ts">
// Uygulama içi bildirimler: model yeni haber veya çıkarım gönderince ya da bir parçanın stoğu sipariş seviyesinin
// altına düşünce (Ayarlar'daki tercihlere göre) düşer.
// Sayfa açıkken dakikada bir ve pencereye dönüldüğünde yenilenir.
const YENILEME_MS = 60_000

const { data, refresh } = await useFetch<BildirimListesi>('/api/bildirimler', {
  key: 'bildirimler',
  default: () => ({ okunmamis: 0, bildirimler: [] })
})

let zamanlayici: ReturnType<typeof setInterval> | undefined
const odaklaninca = () => refresh()
onMounted(() => {
  zamanlayici = setInterval(refresh, YENILEME_MS)
  window.addEventListener('focus', odaklaninca)
})
onBeforeUnmount(() => {
  clearInterval(zamanlayici)
  window.removeEventListener('focus', odaklaninca)
})

const acik = ref(false)
const { t, goreli, sayi } = useDil()
const TUR: Record<BildirimTuru, { anahtar: string, icon: string }> = {
  yeni_olay: { anahtar: 'bildirim.yeniHaber', icon: 'i-lucide-newspaper' },
  yeni_cikarim: { anahtar: 'bildirim.modelCikarimi', icon: 'i-lucide-bot' },
  siparis_gerekli: { anahtar: 'bildirim.siparisGerekli', icon: 'i-lucide-package' }
}

// Stok bildiriminin metni arayüz dilinde yazılır; olay bildiriminde modelin metni gösterilir
function mesaj(b: Bildirim) {
  return b.stok
    ? t('bildirim.stokMesaj', { a: sayi(b.stok.kullanilabilir), b: sayi(b.stok.siparisSeviyesi) })
    : b.mesaj
}

function neZaman(iso: string) {
  const dakika = Math.round((Date.parse(iso) - Date.now()) / 60_000)
  if (Math.abs(dakika) < 60) return goreli(dakika, 'minute')
  const saat = Math.round(dakika / 60)
  if (Math.abs(saat) < 24) return goreli(saat, 'hour')
  return goreli(Math.round(saat / 24), 'day')
}

async function ac(b: Bildirim) {
  acik.value = false
  if (!b.okundu) {
    await $fetch('/api/bildirimler/okundu', { method: 'POST', body: { id: b.id } })
    await refresh()
  }
  await navigateTo(b.stok
    ? { path: '/tedarikciler', query: { stok: 'siparis_gerekli', sirala: 'stok' } }
    : { path: '/olaylar', query: { olay: b.olayId } })
}

async function tumunuOkundu() {
  await $fetch('/api/bildirimler/okundu', { method: 'POST', body: {} })
  await refresh()
}
</script>

<template>
  <UPopover v-model:open="acik" :content="{ align: 'end' }">
    <UChip :text="data.okunmamis > 9 ? '9+' : data.okunmamis" :show="data.okunmamis > 0" color="error" size="3xl">
      <UButton
        color="neutral"
        variant="ghost"
        square
        icon="i-lucide-bell"
        :aria-label="data.okunmamis ? t('bildirim.okunmamis', { n: data.okunmamis }) : t('bildirim.baslik')"
      />
    </UChip>

    <template #content>
      <div class="w-[min(24rem,calc(100vw-2rem))]">
        <div class="flex items-center justify-between gap-2 border-b border-default px-4 py-3">
          <p class="font-semibold text-highlighted">{{ t('bildirim.baslik') }}</p>
          <UButton
            v-if="data.okunmamis"
            size="xs"
            variant="link"
            :label="t('bildirim.tumunuOkundu')"
            @click="tumunuOkundu"
          />
        </div>

        <p v-if="!data.bildirimler.length" class="px-4 py-6 text-center text-sm text-muted">
          {{ t('bildirim.yok') }}
        </p>

        <ul v-else class="max-h-[60vh] overflow-y-auto divide-y divide-default">
          <li v-for="b in data.bildirimler" :key="b.id">
            <button
              type="button"
              class="w-full text-left seviye-serit px-4 py-3 transition-colors hover:bg-elevated/60"
              :class="[`seviye-serit--${b.seviye}`, b.okundu ? 'opacity-70' : 'bg-elevated/30']"
              @click="ac(b)"
            >
              <div class="flex items-center justify-between gap-2 text-xs text-muted">
                <span class="flex items-center gap-1 font-medium" :class="b.tur === 'yeni_cikarim' ? 'text-primary' : b.tur === 'siparis_gerekli' ? 'text-warning' : ''">
                  <UIcon :name="TUR[b.tur].icon" class="size-3.5" />
                  {{ t(TUR[b.tur].anahtar) }}
                </span>
                <span class="flex items-center gap-1.5">
                  {{ neZaman(b.olusturma) }}
                  <span v-if="!b.okundu" class="inline-block size-2 rounded-full bg-[var(--ui-primary)]" :aria-label="t('bildirim.okunmadi')" />
                </span>
              </div>
              <div class="mt-1 flex items-start justify-between gap-2">
                <p class="text-sm font-medium text-highlighted line-clamp-2">{{ b.baslik }}</p>
                <SeviyeRozeti :seviye="b.seviye" class="shrink-0" />
              </div>
              <p class="mt-0.5 text-sm text-toned line-clamp-2">{{ mesaj(b) }}</p>
            </button>
          </li>
        </ul>

        <div class="border-t border-default px-4 py-2 text-xs text-muted">
          {{ t('bildirim.ayarNotu') }} <ULink to="/ayarlar" class="text-primary" @click="acik = false">{{ t('nav.ayarlar') }}</ULink>{{ t('bildirim.ayarNotuSon') }}
        </div>
      </div>
    </template>
  </UPopover>
</template>
