<script setup lang="ts">
// Uygulama içi bildirimler: model yeni haber veya çıkarım gönderince (Ayarlar'daki tercihlere göre) düşer.
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
const TUR_ETIKETI: Record<BildirimTuru, { etiket: string, icon: string }> = {
  yeni_olay: { etiket: 'Yeni haber', icon: 'i-lucide-newspaper' },
  yeni_cikarim: { etiket: 'Model çıkarımı', icon: 'i-lucide-bot' }
}

const goreli = new Intl.RelativeTimeFormat('tr', { numeric: 'auto' })
function neZaman(iso: string) {
  const dakika = Math.round((Date.parse(iso) - Date.now()) / 60_000)
  if (Math.abs(dakika) < 60) return goreli.format(dakika, 'minute')
  const saat = Math.round(dakika / 60)
  if (Math.abs(saat) < 24) return goreli.format(saat, 'hour')
  return goreli.format(Math.round(saat / 24), 'day')
}

async function ac(b: Bildirim) {
  acik.value = false
  if (!b.okundu) {
    await $fetch('/api/bildirimler/okundu', { method: 'POST', body: { id: b.id } })
    await refresh()
  }
  await navigateTo({ path: '/olaylar', query: { olay: b.olayId } })
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
        :aria-label="data.okunmamis ? `Bildirimler, ${data.okunmamis} okunmamış` : 'Bildirimler'"
      />
    </UChip>

    <template #content>
      <div class="w-[min(24rem,calc(100vw-2rem))]">
        <div class="flex items-center justify-between gap-2 border-b border-default px-4 py-3">
          <p class="font-semibold text-highlighted">Bildirimler</p>
          <UButton
            v-if="data.okunmamis"
            size="xs"
            variant="link"
            label="Tümünü okundu say"
            @click="tumunuOkundu"
          />
        </div>

        <p v-if="!data.bildirimler.length" class="px-4 py-6 text-center text-sm text-muted">
          Henüz bildirim yok. Model yeni bir haber veya çıkarım gönderdiğinde burada görünecek.
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
                <span class="flex items-center gap-1 font-medium" :class="b.tur === 'yeni_cikarim' ? 'text-primary' : ''">
                  <UIcon :name="TUR_ETIKETI[b.tur].icon" class="size-3.5" />
                  {{ TUR_ETIKETI[b.tur].etiket }}
                </span>
                <span class="flex items-center gap-1.5">
                  {{ neZaman(b.olusturma) }}
                  <span v-if="!b.okundu" class="inline-block size-2 rounded-full bg-[var(--ui-primary)]" aria-label="okunmadı" />
                </span>
              </div>
              <div class="mt-1 flex items-start justify-between gap-2">
                <p class="text-sm font-medium text-highlighted line-clamp-2">{{ b.baslik }}</p>
                <SeviyeRozeti :seviye="b.seviye" class="shrink-0" />
              </div>
              <p class="mt-0.5 text-sm text-toned line-clamp-2">{{ b.mesaj }}</p>
            </button>
          </li>
        </ul>

        <div class="border-t border-default px-4 py-2 text-xs text-muted">
          Hangi bildirimlerin geleceği <ULink to="/ayarlar" class="text-primary" @click="acik = false">Ayarlar</ULink>'dan seçilir.
        </div>
      </div>
    </template>
  </UPopover>
</template>
