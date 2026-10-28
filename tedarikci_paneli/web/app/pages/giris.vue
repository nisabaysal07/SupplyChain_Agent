<script setup lang="ts">
import type { FormSubmitEvent } from '@nuxt/ui'
import type { z } from 'zod'

definePageMeta({ layout: false })
const { t } = useDil()
useHead({ title: () => t('giris.sayfaBasligi') })

const route = useRoute()
const { fetch: oturumuYenile } = useUserSession()

const form = reactive({ eposta: '', sifre: '' })
// Hata sözlük anahtarı olarak tutulur: dil değişince mesaj da değişir
const hata = ref('')
const gonderiliyor = ref(false)

async function gonder(e: FormSubmitEvent<z.output<typeof GirisSemasi>>) {
  hata.value = ''
  gonderiliyor.value = true
  try {
    await $fetch('/api/auth/giris', { method: 'POST', body: e.data })
    await oturumuYenile()
    await navigateTo(guvenliYonlendirme(route.query.yonlendir), { replace: true })
  }
  catch (err) {
    const durum = (err as { statusCode?: number }).statusCode
    hata.value = durum === 429 ? 'giris.cokDeneme' : durum === 401 ? 'giris.hatali' : 'giris.hata'
  }
  finally {
    gonderiliyor.value = false
  }
}
</script>

<template>
  <main class="relative min-h-dvh flex items-center justify-center bg-muted px-4">
    <DilSecici class="absolute top-4 right-4" />

    <UCard class="w-full max-w-sm belir">
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-shield-check" class="size-7 text-primary" />
          <div>
            <h1 class="font-semibold text-highlighted">ChainGuard AI</h1>
            <p class="text-sm text-muted">{{ t('giris.altBaslik') }}</p>
          </div>
        </div>
      </template>

      <UForm :schema="GirisSemasi" :state="form" class="space-y-4" @submit="gonder">
        <UFormField :label="t('giris.eposta')" name="eposta">
          <UInput v-model="form.eposta" type="email" autocomplete="username" class="w-full" autofocus />
          <template #error="{ error }">{{ typeof error === 'string' ? t(error) : '' }}</template>
        </UFormField>
        <UFormField :label="t('giris.sifre')" name="sifre">
          <UInput v-model="form.sifre" type="password" autocomplete="current-password" class="w-full" />
          <template #error="{ error }">{{ typeof error === 'string' ? t(error) : '' }}</template>
        </UFormField>

        <UAlert v-if="hata" class="belir" color="error" variant="subtle" icon="i-lucide-circle-alert" :title="t(hata)" />

        <UButton type="submit" :label="t('giris.girisYap')" block :loading="gonderiliyor" />
      </UForm>
    </UCard>
  </main>
</template>
