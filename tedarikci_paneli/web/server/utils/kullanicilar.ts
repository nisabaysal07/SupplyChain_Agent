import { randomUUID } from 'node:crypto'

// Kullanıcı kayıtları Nitro deposunda tutulur (nuxt.config.ts → nitro.storage.veri, .data/veri klasörü).
// Şifre yalnızca scrypt özeti olarak saklanır; özet hiçbir API yanıtına konmaz.

export interface KullaniciKaydi extends Kullanici {
  sifreHash: string
  olusturma: string
}

const depo = () => useStorage<KullaniciKaydi>('veri')
const anahtar = (id: string) => `kullanici:${id}`

const VARSAYILAN_BILDIRIMLER: BildirimTercihleri = { eposta: true, uygulamaIci: true, seviyeler: ['yuksek', 'orta'] }

export function disaAc(k: KullaniciKaydi): Kullanici {
  const { id, ad, soyad, eposta, rol, bildirimler } = k
  return { id, ad, soyad, eposta, rol, bildirimler }
}

export function oturumBilgisi(k: KullaniciKaydi) {
  const { id, ad, soyad, eposta, rol } = k
  return { id, ad, soyad, eposta, rol }
}

export async function kullaniciGetir(id: string): Promise<KullaniciKaydi | null> {
  return await depo().getItem(anahtar(id))
}

export async function kullanicilariListele(): Promise<KullaniciKaydi[]> {
  const anahtarlar = await depo().getKeys('kullanici')
  const kayitlar = await Promise.all(anahtarlar.map(a => depo().getItem(a)))
  return kayitlar.filter((k): k is KullaniciKaydi => k !== null)
}

export async function epostaIleBul(eposta: string): Promise<KullaniciKaydi | null> {
  const e = eposta.trim().toLowerCase()
  return (await kullanicilariListele()).find(k => k.eposta === e) ?? null
}

export async function kullaniciKaydet(k: KullaniciKaydi): Promise<void> {
  await depo().setItem(anahtar(k.id), k)
}

export async function kullaniciOlustur(veri: { ad: string, soyad: string, eposta: string, rol: Rol, sifre: string }) {
  const kayit: KullaniciKaydi = {
    id: randomUUID(),
    ad: veri.ad,
    soyad: veri.soyad,
    eposta: veri.eposta.trim().toLowerCase(),
    rol: veri.rol,
    bildirimler: VARSAYILAN_BILDIRIMLER,
    sifreHash: await hashPassword(veri.sifre),
    olusturma: new Date().toISOString()
  }
  await kullaniciKaydet(kayit)
  return kayit
}

// Sistem ayarları tüm kullanıcılar için ortaktır
const SISTEM_ANAHTARI = 'sistem:ayarlar'
const VARSAYILAN_SISTEM: SistemAyarlari = { senkronizasyonSaat: 12 }

export async function sistemAyarlariGetir(): Promise<SistemAyarlari> {
  const kayit = await useStorage<SistemAyarlari>('veri').getItem(SISTEM_ANAHTARI)
  return { ...VARSAYILAN_SISTEM, ...kayit }
}

export async function sistemAyarlariKaydet(ayarlar: SistemAyarlari): Promise<void> {
  await useStorage<SistemAyarlari>('veri').setItem(SISTEM_ANAHTARI, ayarlar)
}
