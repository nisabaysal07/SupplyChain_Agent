<script setup lang="ts">
import { tr } from '@nuxt/ui/locale'
</script>

<template>
  <UApp :locale="tr">
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
