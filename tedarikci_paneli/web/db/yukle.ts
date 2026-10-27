// CSV'leri PostgreSQL'e yükler.  Çalıştırma (web/ klasöründe):  npm run db:yukle
//
// Bağlantı: VERITABANI_YUKLEME_URL (tablo oluşturma/yazma yetkili kullanıcı) yoksa NUXT_DATABASE_URL.
// CSV klasörü: NUXT_VERI_KLASORU yoksa web/ klasörünün bir üstü.
import { resolve } from 'node:path'
import pg from 'pg'
import { csvleriYukle } from './yukleyici.ts'

const baglanti = process.env.VERITABANI_YUKLEME_URL || process.env.NUXT_DATABASE_URL
if (!baglanti) {
  console.error('VERITABANI_YUKLEME_URL veya NUXT_DATABASE_URL tanımlı değil (web/.env).')
  process.exit(1)
}
const klasor = process.env.NUXT_VERI_KLASORU || resolve(import.meta.dirname, '..', '..')

const istemci = new pg.Client({ connectionString: baglanti, connectionTimeoutMillis: 10_000 })
try {
  await istemci.connect()
  const sayilar = await csvleriYukle(istemci, klasor)
  console.log('Yüklendi:', Object.entries(sayilar).map(([t, n]) => `${t} ${n}`).join(' · '))
}
catch (e) {
  // Bağlantı adresi (şifre içerebilir) yazdırılmaz
  console.error('Yükleme başarısız, veritabanı değişmedi:', (e as Error).message)
  process.exitCode = 1
}
finally {
  await istemci.end()
}
