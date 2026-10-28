import { createHash } from 'node:crypto'
import type { Storage } from 'unstorage'

// Hesap başına hatalı giriş sınırı: 15 dakika içinde 5 hatalı deneme o e-postayı 15 dakika kilitler.
// IP başına hız sınırı (nuxt-security) adres değiştiren saldırganı durdurmaz; bu sınır e-postaya bağlıdır.
// Kayıtlı olmayan e-postalar da sayılır: kilit, e-postanın kayıtlı olup olmadığını belli etmez.
// Deneme şifre kontrolünden ÖNCE sayılır, başarılı girişte sıfırlanır: aynı anda gönderilen denemeler de sınırı aşamaz.
// Not: sayaç tek sunucu süreci içinde sırayla güncellenir; birden çok süreç aynı depoyu paylaşırsa sınır gevşeyebilir.

export const EN_FAZLA_HATA = 5
export const KILIT_SURESI_MS = 15 * 60_000

interface Sayac {
  hatalar: number
  ilkHata: number
  kilitBitis: number | null
}

// Aynı e-postanın sayacı sırayla okunup yazılır (oku-artır-yaz yarışı olmasın)
const kuyruklar = new Map<string, Promise<unknown>>()
function sirayla<T>(anahtar: string, is: () => Promise<T>): Promise<T> {
  const sonuc = (kuyruklar.get(anahtar) ?? Promise.resolve()).then(is, is)
  const kuyruk = sonuc.catch(() => {})
  kuyruklar.set(anahtar, kuyruk)
  kuyruk.then(() => {
    if (kuyruklar.get(anahtar) === kuyruk) kuyruklar.delete(anahtar)
  })
  return sonuc
}

export function girisKilidiOlustur(depo: Storage, saat = () => Date.now()) {
  // E-posta anahtara düz yazılmaz (depo anahtarında ':' ayraçtır, e-posta diskte açıkça durmasın)
  const anahtar = (eposta: string) => `girisKilidi:${createHash('sha256').update(eposta).digest('hex')}`

  return {
    // Denemeyi sayar; e-posta kilitliyse false (o zaman şifre doğru olsa da giriş reddedilir)
    async denemeBaslat(eposta: string): Promise<boolean> {
      const a = anahtar(eposta)
      return sirayla(a, async () => {
        const simdi = saat()
        let s = await depo.getItem<Sayac>(a)
        if (s?.kilitBitis && simdi < s.kilitBitis) return false
        // Kilit bitti ya da ilk hatanın üstünden 15 dakika geçti: sayım baştan
        if (!s || s.kilitBitis || simdi - s.ilkHata >= KILIT_SURESI_MS) s = { hatalar: 0, ilkHata: simdi, kilitBitis: null }
        s.hatalar++
        if (s.hatalar >= EN_FAZLA_HATA) s.kilitBitis = simdi + KILIT_SURESI_MS
        await depo.setItem(a, s)
        return true
      })
    },
    // Başarılı giriş: sayaç (ve bu denemenin koyduğu kilit) silinir
    async basarili(eposta: string): Promise<void> {
      const a = anahtar(eposta)
      await sirayla(a, () => depo.removeItem(a))
    }
  }
}

let varsayilan: ReturnType<typeof girisKilidiOlustur> | undefined
export const girisKilidi = () => (varsayilan ??= girisKilidiOlustur(useStorage('veri')))
