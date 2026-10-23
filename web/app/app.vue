<script setup lang="ts">
const file = ref<File | null>(null)
const loading = ref(false)
const error = ref('')
const report = ref<any>(null)

const tableLabels: Record<string, string> = {
  items: 'Ürünler (items)',
  suppliers: 'Tedarikçiler (suppliers)',
  supplier_items: 'Tedarikçi ürünleri (supplier_items)',
  contracts: 'Sözleşmeler (contracts)',
  shipments: 'Sevkiyatlar (shipments)',
  inventory: 'Stok (inventory)',
}

function onFileChange(e: Event) {
  file.value = (e.target as HTMLInputElement).files?.[0] ?? null
  report.value = null
  error.value = ''
}

async function upload() {
  if (!file.value) return
  loading.value = true
  error.value = ''
  report.value = null
  const form = new FormData()
  form.append('file', file.value)
  try {
    report.value = await $fetch('/api/upload', { method: 'POST', body: form })
  } catch (e: any) {
    error.value = e?.data?.data?.message ?? e?.data?.message ?? 'Yükleme sırasında bir hata oluştu.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="page">
    <h1>Tedarik Excel'i Yükle</h1>
    <p class="hint">
      <strong>company_file</strong> sayfası olan .xlsx dosyanızı seçin. Veritabanında zaten
      bulunan kayıtlar tekrar eklenmez, sadece yeni olanlar eklenir.
    </p>

    <form class="card" @submit.prevent="upload">
      <input type="file" accept=".xlsx" @change="onFileChange" />
      <button type="submit" :disabled="!file || loading">
        {{ loading ? 'Yükleniyor…' : 'Yükle' }}
      </button>
    </form>

    <p v-if="error" class="error">{{ error }}</p>

    <section v-if="report" class="card">
      <h2>Sonuç</h2>
      <p>
        {{ report.totalRows }} satırdan <strong>{{ report.importedRows }}</strong> tanesi işlendi.
        <span v-if="report.errors.length" class="error-text">{{ report.errors.length }} satır hatalı.</span>
      </p>

      <table>
        <thead>
          <tr><th>Tablo</th><th>Yeni eklenen</th><th>Zaten vardı</th></tr>
        </thead>
        <tbody>
          <tr v-for="(label, key) in tableLabels" :key="key">
            <td>{{ label }}</td>
            <td class="num">{{ report.inserted[key] }}</td>
            <td class="num">{{ report.alreadyExisted[key] }}</td>
          </tr>
        </tbody>
      </table>

      <div v-if="report.errors.length">
        <h3>Eklenemeyen satırlar</h3>
        <ul>
          <li v-for="e in report.errors" :key="e.row">Satır {{ e.row }}: {{ e.message }}</li>
        </ul>
      </div>
    </section>
  </main>
</template>

<style>
body { margin: 0; font-family: system-ui, sans-serif; background: #f5f6f8; color: #1f2328; }
.page { max-width: 720px; margin: 40px auto; padding: 0 16px; }
h1 { margin-bottom: 8px; }
.hint { color: #57606a; }
.card { background: #fff; border: 1px solid #d0d7de; border-radius: 8px; padding: 20px; margin-top: 16px; }
form.card { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
button { padding: 8px 18px; border: 0; border-radius: 6px; background: #1f6feb; color: #fff; cursor: pointer; font-size: 15px; }
button:disabled { background: #8c959f; cursor: default; }
table { width: 100%; border-collapse: collapse; margin-top: 8px; }
th, td { text-align: left; padding: 8px; border-bottom: 1px solid #eaeef2; }
.num { text-align: right; }
.error { background: #ffebe9; color: #a40e26; padding: 12px; border-radius: 6px; margin-top: 16px; }
.error-text { color: #a40e26; }
</style>
