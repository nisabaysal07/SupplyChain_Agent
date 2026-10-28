<script setup lang="ts">
import { en, tr } from '@nuxt/ui/locale'

// Nuxt UI bileşenlerinin kendi metinleri (tablo boş, kapat vb.) ve <html lang> seçili dili izler
const { dil } = useDil()
useHead({ htmlAttrs: { lang: dil } })
</script>

<template>
  <UApp :locale="dil === 'tr' ? tr : en">
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
