<script setup lang="ts">
import type { DropdownMenuItem, NavigationMenuItem } from '@nuxt/ui'

const { user, clear } = useUserSession()

const menu: NavigationMenuItem[] = [
  { label: 'Kontrol Paneli', icon: 'i-lucide-layout-dashboard', to: '/' },
  { label: 'Tedarikçiler', icon: 'i-lucide-users', to: '/tedarikciler' },
  { label: 'Olaylar', icon: 'i-lucide-circle-alert', to: '/olaylar' }
]

const altMenu: NavigationMenuItem[] = [
  { label: 'Ayarlar', icon: 'i-lucide-settings', to: '/ayarlar' }
]

const tamAd = computed(() => [user.value?.ad, user.value?.soyad].filter(Boolean).join(' '))

async function cikisYap() {
  await clear()
  await navigateTo('/giris')
}

const kullaniciMenusu = computed<DropdownMenuItem[][]>(() => [
  [{ label: user.value?.eposta ?? '', type: 'label' }],
  [{ label: 'Ayarlar', icon: 'i-lucide-settings', to: '/ayarlar' }],
  [{ label: 'Oturumu kapat', icon: 'i-lucide-log-out', color: 'error', onSelect: cikisYap }]
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
            :aria-label="`Kullanıcı menüsü: ${tamAd}`"
          >
            <UAvatar :alt="tamAd" size="xs" />
            <span v-if="!collapsed" class="min-w-0 text-left">
              <span class="block truncate font-medium text-highlighted">{{ tamAd }}</span>
              <span class="block truncate text-xs text-muted">{{ user?.rol === 'yonetici' ? 'Yönetici' : 'İzleyici' }}</span>
            </span>
            <UIcon v-if="!collapsed" name="i-lucide-chevrons-up-down" class="ms-auto size-4 text-muted" />
          </UButton>
        </UDropdownMenu>
      </template>
    </UDashboardSidebar>

    <slot />
  </UDashboardGroup>
</template>
