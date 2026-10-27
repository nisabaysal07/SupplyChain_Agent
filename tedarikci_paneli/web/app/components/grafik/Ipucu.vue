<script setup lang="ts">
import type { IpucuSatiri } from '~/composables/useIpucu'

const props = defineProps<{ gorunur: boolean, x: number, y: number, baslik: string, satirlar: IpucuSatiri[] }>()

// Kutu imlecin üstünde durur; kapsayıcının sağ yarısındaysa sola açılır
const stil = computed(() => ({
  left: `${props.x}px`,
  top: `${props.y}px`,
  transform: `translate(${props.x > 220 ? 'calc(-100% - 12px)' : '12px'}, calc(-100% - 8px))`
}))
</script>

<template>
  <div
    v-show="gorunur"
    role="tooltip"
    class="pointer-events-none absolute z-10 min-w-40 max-w-72 rounded-md border border-default bg-default px-3 py-2 text-xs shadow-lg"
    :style="stil"
  >
    <p class="font-semibold text-highlighted">{{ baslik }}</p>
    <dl class="mt-1 space-y-0.5">
      <div v-for="s in satirlar" :key="s.ad" class="flex items-center justify-between gap-4">
        <dt class="flex items-center gap-1.5 text-muted">
          <span v-if="s.renk" class="inline-block size-2 rounded-full" :style="{ background: s.renk }" />
          {{ s.ad }}
        </dt>
        <dd class="font-medium text-highlighted tabular-nums">{{ s.deger }}</dd>
      </div>
    </dl>
  </div>
</template>
