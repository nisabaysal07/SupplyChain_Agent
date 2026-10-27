import { randomUUID } from 'node:crypto'

// Bildirimler kullanıcı başına tutulur: .data/veri/bildirim/<kullaniciId>/<bildirimId>
// Her kullanıcının en yeni 100 bildirimi saklanır.

const EN_FAZLA = 100
const depo = () => useStorage<Bildirim>('veri')
const onEk = (kullaniciId: string) => `bildirim:${kullaniciId}`

async function kullanicininBildirimleri(kullaniciId: string): Promise<{ anahtar: string, b: Bildirim }[]> {
  const anahtarlar = await depo().getKeys(onEk(kullaniciId))
  const kayitlar = await Promise.all(anahtarlar.map(async a => ({ anahtar: a, b: await depo().getItem(a) })))
  return kayitlar
    .filter((k): k is { anahtar: string, b: Bildirim } => k.b !== null)
    .sort((x, y) => y.b.olusturma.localeCompare(x.b.olusturma))
}

export async function bildirimleriGetir(kullaniciId: string, adet = 30): Promise<BildirimListesi> {
  const hepsi = await kullanicininBildirimleri(kullaniciId)
  return {
    okunmamis: hepsi.filter(k => !k.b.okundu).length,
    bildirimler: hepsi.slice(0, adet).map(k => k.b)
  }
}

// Model olay gönderince çağrılır; bildirim düşen kullanıcı sayısını döner
export async function olayBildirimiGonder(onceki: KayitliOlay | null, olay: KayitliOlay): Promise<number> {
  const tur = bildirimTuruBul(onceki, olay, bugunISO())
  if (!tur) return 0
  const { seviye, mesaj } = bildirimIcerigi(olay)
  const alicilar = (await kullanicilariListele()).filter(k => kullaniciIstiyorMu(k.bildirimler, seviye))

  const olusturma = new Date().toISOString()
  await Promise.all(alicilar.map(async (k) => {
    const id = randomUUID()
    await depo().setItem(`${onEk(k.id)}:${id}`, {
      id, olayId: olay.id, tur, seviye, baslik: olay.baslik, mesaj, olusturma, okundu: false
    })
    // Eski bildirimleri temizle
    const fazlalar = (await kullanicininBildirimleri(k.id)).slice(EN_FAZLA)
    await Promise.all(fazlalar.map(f => depo().removeItem(f.anahtar)))
  }))
  return alicilar.length
}

// id verilmezse kullanıcının bütün bildirimleri okundu sayılır
export async function okunduIsaretle(kullaniciId: string, id?: string): Promise<void> {
  const hedefler = (await kullanicininBildirimleri(kullaniciId)).filter(k => !k.b.okundu && (!id || k.b.id === id))
  await Promise.all(hedefler.map(k => depo().setItem(k.anahtar, { ...k.b, okundu: true })))
}

// Olay silinince ona ait bildirimler de silinir (tıklanınca boş sayfaya gitmesin)
export async function olayBildirimleriniSil(olayId: string): Promise<void> {
  const anahtarlar = await depo().getKeys('bildirim')
  await Promise.all(anahtarlar.map(async (a) => {
    if ((await depo().getItem(a))?.olayId === olayId) await depo().removeItem(a)
  }))
}
