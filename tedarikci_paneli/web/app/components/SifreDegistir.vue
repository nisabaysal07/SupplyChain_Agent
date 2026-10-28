<script setup lang="ts">
import type { FormSubmitEvent } from '@nuxt/ui'
import type { z } from 'zod'

const acik = defineModel<boolean>('open', { default: false })
const toast = useToast()
const { t } = useDil()

const bos = () => ({ mevcut: '', yeni: '', tekrar: '' })
const form = reactive(bos())
// Hata sözlük anahtarı olarak tutulur: dil değişince mesaj da değişir
const hata = ref('')
const gonderiliyor = ref(false)

watch(acik, (v) => {
  if (v) {
    Object.assign(form, bos())
    hata.value = ''
  }
})

async function gonder(e: FormSubmitEvent<z.output<typeof SifreSemasi>>) {
  hata.value = ''
  gonderiliyor.value = true
  try {
    await $fetch('/api/profil/sifre', { method: 'POST', body: e.data })
    acik.value = false
    toast.add({ title: t('sifre.degisti'), color: 'success', icon: 'i-lucide-check' })
  }
  catch (err) {
    hata.value = (err as { statusMessage?: string }).statusMessage === 'Mevcut şifre hatalı'
      ? 'sifre.mevcutHatali'
      : 'sifre.hata'
  }
  finally {
    gonderiliyor.value = false
  }
}
</script>

<template>
  <UModal v-model:open="acik" :title="t('sifre.baslik')" :description="t('sifre.aciklama')">
    <template #body>
      <UForm id="sifre-formu" :schema="SifreSemasi" :state="form" class="space-y-4" @submit="gonder">
        <UFormField :label="t('sifre.mevcut')" name="mevcut">
          <UInput v-model="form.mevcut" type="password" autocomplete="current-password" class="w-full" />
          <template #error="{ error }">{{ typeof error === 'string' ? t(error) : '' }}</template>
        </UFormField>
        <UFormField :label="t('sifre.yeni')" name="yeni">
          <UInput v-model="form.yeni" type="password" autocomplete="new-password" class="w-full" />
          <template #error="{ error }">{{ typeof error === 'string' ? t(error) : '' }}</template>
        </UFormField>
        <UFormField :label="t('sifre.tekrar')" name="tekrar">
          <UInput v-model="form.tekrar" type="password" autocomplete="new-password" class="w-full" />
          <template #error="{ error }">{{ typeof error === 'string' ? t(error) : '' }}</template>
        </UFormField>
        <UAlert v-if="hata" color="error" variant="subtle" icon="i-lucide-circle-alert" :title="t(hata)" />
      </UForm>
    </template>
    <template #footer>
      <div class="flex justify-end gap-2 w-full">
        <UButton :label="t('genel.vazgec')" color="neutral" variant="ghost" @click="acik = false" />
        <UButton type="submit" form="sifre-formu" :label="t('sifre.degistir')" :loading="gonderiliyor" />
      </div>
    </template>
  </UModal>
</template>
