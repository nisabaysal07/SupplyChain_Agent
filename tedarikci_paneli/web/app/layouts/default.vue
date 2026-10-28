<script setup lang="ts">
import type { DropdownMenuItem, NavigationMenuItem } from '@nuxt/ui'

const { user, clear } = useUserSession()
const { t } = useDil()

const menu = computed<NavigationMenuItem[]>(() => [
  { label: t('nav.pano'), icon: 'i-lucide-layout-dashboard', to: '/' },
  { label: t('nav.tedarikciler'), icon: 'i-lucide-users', to: '/tedarikciler' },
  { label: t('nav.olaylar'), icon: 'i-lucide-circle-alert', to: '/olaylar' },
  // Veritabanına yazdığı için yalnızca yöneticiye görünür
  ...(user.value?.rol === 'yonetici' ? [{ label: t('nav.yukleme'), icon: 'i-lucide-upload', to: '/yukleme' }] : [])
])

const altMenu = computed<NavigationMenuItem[]>(() => [
  { label: t('nav.ayarlar'), icon: 'i-lucide-settings', to: '/ayarlar' }
])

const tamAd = computed(() => [user.value?.ad, user.value?.soyad].filter(Boolean).join(' '))

async function cikisYap() {
  await clear()
  await navigateTo('/giris')
}

const kullaniciMenusu = computed<DropdownMenuItem[][]>(() => [
  [{ label: user.value?.eposta ?? '', type: 'label' }],
  [{ label: t('nav.ayarlar'), icon: 'i-lucide-settings', to: '/ayarlar' }],
  [{ label: t('nav.cikis'), icon: 'i-lucide-log-out', color: 'error', onSelect: cikisYap }]
])
</script>

<template>
  <UDashboardGroup>
    <UDashboardSidebar collapsible :ui="{ footer: 'border-t border-default' }">
      <template #header="{ collapsed }">
        <NuxtLink to="/" class="flex items-center gap-2 font-semibold">
          <UIcon name="i-lucide-shield-check" class="size-6 text-primary shrink-0" />
          <span v-if="!collapsed">ChainGuard AI</span>
        </NuxtLink>
      </template>

      <template #default="{ collapsed }">
        <UNavigationMenu :collapsed="collapsed" :items="menu" orientation="vertical" />
        <UNavigationMenu :collapsed="collapsed" :items="altMenu" orientation="vertical" class="mt-auto" />
      </template>

      <template #footer="{ collapsed }">
        <UDropdownMenu :items="kullaniciMenusu" :content="{ align: 'start', side: 'top' }" class="w-full">
          <UButton
            color="neutral"
            variant="ghost"
            block
            :square="collapsed"
            class="justify-start"
            :aria-label="t('nav.kullaniciMenusu', { ad: tamAd })"
          >
            <UAvatar :alt="tamAd" size="xs" />
            <span v-if="!collapsed" class="min-w-0 text-left">
              <span class="block truncate font-medium text-highlighted">{{ tamAd }}</span>
              <span class="block truncate text-xs text-muted">{{ t(user?.rol === 'yonetici' ? 'rol.yonetici' : 'rol.izleyici') }}</span>
            </span>
            <UIcon v-if="!collapsed" name="i-lucide-chevrons-up-down" class="ms-auto size-4 text-muted" />
          </UButton>
        </UDropdownMenu>
      </template>
    </UDashboardSidebar>

    <slot />
  </UDashboardGroup>
</template>
