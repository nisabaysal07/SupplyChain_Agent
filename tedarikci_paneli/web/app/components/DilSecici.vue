<script setup lang="ts">
// Arayüz dili seçimi (English / Türkçe). Seçim çerezde saklanır, sayfa yenilenince de korunur.
const { dil, dilSec, t } = useDil()

const secenekler = [
  { label: 'English', value: 'en' },
  { label: 'Türkçe', value: 'tr' }
]
const secili = computed({
  get: () => dil.value,
  set: (v: string) => dilSec(v === 'tr' ? 'tr' : 'en')
})
</script>

<template>
  <USelect
    v-model="secili"
    :items="secenekler"
    icon="i-lucide-languages"
    color="neutral"
    variant="ghost"
    :aria-label="t('genel.dil')"
    class="w-32"
  />
</template>
