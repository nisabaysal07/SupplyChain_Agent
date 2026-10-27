<script setup lang="ts">
import type { FormSubmitEvent } from '@nuxt/ui'
import type { z } from 'zod'

definePageMeta({ layout: false })
useHead({ title: 'Giriş · ChainGuard AI' })

const route = useRoute()
const { fetch: oturumuYenile } = useUserSession()

const form = reactive({ eposta: '', sifre: '' })
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
    hata.value = durum === 429
      ? 'Çok fazla deneme yapıldı. Bir dakika sonra tekrar deneyin.'
      : durum === 401 ? 'E-posta veya şifre hatalı.' : 'Giriş yapılamadı. Lütfen tekrar deneyin.'
  }
  finally {
    gonderiliyor.value = false
  }
}
</script>

<template>
  <main class="min-h-dvh flex items-center justify-center bg-muted px-4">
    <UCard class="w-full max-w-sm belir">
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-shield-check" class="size-7 text-primary" />
          <div>
            <h1 class="font-semibold text-highlighted">ChainGuard AI</h1>
            <p class="text-sm text-muted">Tedarik zinciri risk paneli</p>
          </div>
        </div>
      </template>

      <UForm :schema="GirisSemasi" :state="form" class="space-y-4" @submit="gonder">
        <UFormField label="E-posta" name="eposta">
          <UInput v-model="form.eposta" type="email" autocomplete="username" class="w-full" autofocus />
        </UFormField>
        <UFormField label="Şifre" name="sifre">
          <UInput v-model="form.sifre" type="password" autocomplete="current-password" class="w-full" />
        </UFormField>

        <UAlert v-if="hata" class="belir" color="error" variant="subtle" icon="i-lucide-circle-alert" :title="hata" />

        <UButton type="submit" label="Giriş yap" block :loading="gonderiliyor" />
      </UForm>
    </UCard>
  </main>
</template>
