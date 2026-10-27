<script setup lang="ts">
import type { FormSubmitEvent } from '@nuxt/ui'
import type { z } from 'zod'

const acik = defineModel<boolean>('open', { default: false })
const toast = useToast()

const bos = () => ({ mevcut: '', yeni: '', tekrar: '' })
const form = reactive(bos())
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
    toast.add({ title: 'Şifreniz değiştirildi', color: 'success', icon: 'i-lucide-check' })
  }
  catch (err) {
    hata.value = (err as { statusMessage?: string }).statusMessage === 'Mevcut şifre hatalı'
      ? 'Mevcut şifre hatalı.'
      : 'Şifre değiştirilemedi. Lütfen tekrar deneyin.'
  }
  finally {
    gonderiliyor.value = false
  }
}
</script>

<template>
  <UModal v-model:open="acik" title="Şifre değiştir" description="Yeni şifre en az 12 karakter olmalı.">
    <template #body>
      <UForm id="sifre-formu" :schema="SifreSemasi" :state="form" class="space-y-4" @submit="gonder">
        <UFormField label="Mevcut şifre" name="mevcut">
          <UInput v-model="form.mevcut" type="password" autocomplete="current-password" class="w-full" />
        </UFormField>
        <UFormField label="Yeni şifre" name="yeni">
          <UInput v-model="form.yeni" type="password" autocomplete="new-password" class="w-full" />
        </UFormField>
        <UFormField label="Yeni şifre (tekrar)" name="tekrar">
          <UInput v-model="form.tekrar" type="password" autocomplete="new-password" class="w-full" />
        </UFormField>
        <UAlert v-if="hata" color="error" variant="subtle" icon="i-lucide-circle-alert" :title="hata" />
      </UForm>
    </template>
    <template #footer>
      <div class="flex justify-end gap-2 w-full">
        <UButton label="Vazgeç" color="neutral" variant="ghost" @click="acik = false" />
        <UButton type="submit" form="sifre-formu" label="Şifreyi değiştir" :loading="gonderiliyor" />
      </div>
    </template>
  </UModal>
</template>
