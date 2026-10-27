<script setup lang="ts">
defineProps<{ baslik: string }>()
</script>

<template>
  <UDashboardPanel>
    <template #header>
      <UDashboardNavbar :title="baslik">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #right>
          <slot name="sag" />
          <BildirimZili />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <slot />
    </template>
  </UDashboardPanel>
</template>
