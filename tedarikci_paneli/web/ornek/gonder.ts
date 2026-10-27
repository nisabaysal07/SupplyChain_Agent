// ornek/olaylar/*.json dosyalarını, modelin yapacağı gibi /api/model/olaylar ucuna gönderir.
// Çalıştırma (web/ klasöründe, sunucu açıkken):  npm run ornek:gonder
//
// Erişim anahtarı: NUXT_MODEL_API_TOKEN (web/.env). Hedef: MODEL_HEDEF_URL (varsayılan http://localhost:3000)
import { readdir, readFile } from 'node:fs/promises'
import { join } from 'node:path'

const anahtar = process.env.NUXT_MODEL_API_TOKEN
if (!anahtar) {
  console.error('NUXT_MODEL_API_TOKEN tanımlı değil (web/.env).')
  process.exit(1)
}
const hedef = `${process.env.MODEL_HEDEF_URL || 'http://localhost:3000'}/api/model/olaylar`
const klasor = join(import.meta.dirname, 'olaylar')

let hata = false
for (const dosya of (await readdir(klasor)).filter(d => d.endsWith('.json')).sort()) {
  const yanit = await fetch(hedef, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${anahtar}`, 'Content-Type': 'application/json' },
    body: await readFile(join(klasor, dosya), 'utf8')
  })
  const govde = await yanit.json().catch(() => ({})) as { durum?: string, uyarilar?: string[], data?: unknown }
  console.log(`${dosya}: ${yanit.status} ${govde.durum ?? JSON.stringify(govde.data ?? govde)}`)
  for (const u of govde.uyarilar ?? []) console.log(`  uyarı: ${u}`)
  if (!yanit.ok) hata = true
}
process.exitCode = hata ? 1 : 0
