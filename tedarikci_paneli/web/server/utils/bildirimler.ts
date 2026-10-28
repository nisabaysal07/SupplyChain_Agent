import { randomUUID } from 'node:crypto'

// Bildirimler kullanıcı başına tutulur: .data/veri/bildirim/<kullaniciId>/<bildirimId>
// İki kaynağı var: modelin gönderdiği olaylar ve sipariş seviyesinin altına düşen stok
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

// Bildirimi, tercihleri bu seviyeyi isteyen her kullanıcıya yazar; bildirim düşen kullanıcı sayısını döner
async function bildirimDusur(icerik: Omit<Bildirim, 'id' | 'olusturma' | 'okundu'>): Promise<number> {
  const alicilar = (await kullanicilariListele()).filter(k => kullaniciIstiyorMu(k.bildirimler, icerik.seviye))
  const olusturma = new Date().toISOString()
  await Promise.all(alicilar.map(async (k) => {
    const id = randomUUID()
    await depo().setItem(`${onEk(k.id)}:${id}`, { ...icerik, id, olusturma, okundu: false })
    // Eski bildirimleri temizle
    const fazlalar = (await kullanicininBildirimleri(k.id)).slice(EN_FAZLA)
    await Promise.all(fazlalar.map(f => depo().removeItem(f.anahtar)))
  }))
  return alicilar.length
}

// Model olay gönderince çağrılır; bildirim düşen kullanıcı sayısını döner
export async function olayBildirimiGonder(onceki: KayitliOlay | null, olay: KayitliOlay): Promise<number> {
  const tur = bildirimTuruBul(onceki, olay, bugunISO())
  if (!tur) return 0
  const { seviye, mesaj } = bildirimIcerigi(olay)
  return await bildirimDusur({ olayId: olay.id, tur, seviye, baslik: olay.baslik, mesaj })
}

// Stok veritabanından okunur (Excel yüklemesi veya başka bir sistem değiştirebilir), bu yüzden sipariş gereken
// parçalar zilin her yenilenmesinde kontrol edilir; en fazla dakikada bir, aynı anda tek kontrol.
// Bir önceki kontrolde sipariş gereken tedarikçiler .data/veri/stok/siparisGerekli'de tutulur.
const STOK_KONTROL_ARASI_MS = 60_000
const STOK_ANAHTARI = 'stok:siparisGerekli'
let sonStokKontrolu = 0
let suankiStokKontrolu: Promise<void> | null = null

export function stokBildirimleriniKontrolEt(): Promise<void> {
  if (suankiStokKontrolu) return suankiStokKontrolu
  if (Date.now() - sonStokKontrolu < STOK_KONTROL_ARASI_MS) return Promise.resolve()
  sonStokKontrolu = Date.now()
  suankiStokKontrolu = (async () => {
    const tedarikciler = await tedarikcileriOku()
    const kayitliDepo = useStorage<number[]>('veri')
    const yeniler = yeniSiparisGerekenler((await kayitliDepo.getItem(STOK_ANAHTARI)) ?? [], tedarikciler)
    for (const t of yeniler) {
      const { seviye, baslik, mesaj } = stokBildirimIcerigi(t)
      await bildirimDusur({
        tur: 'siparis_gerekli',
        stok: { tedarikciId: t.id, kullanilabilir: t.stok.kullanilabilir, siparisSeviyesi: t.stok.siparisSeviyesi },
        seviye, baslik, mesaj
      })
    }
    // Toparlanan parçalar listeden çıkar: yeniden düşerlerse yine bildirilir
    await kayitliDepo.setItem(STOK_ANAHTARI, tedarikciler.filter(t => t.stok.durum === 'siparis_gerekli').map(t => t.id))
  })()
    .catch((e) => {
      // Veritabanı kapalıysa olay bildirimleri yine çalışsın
      console.error('[ChainGuard] Stok bildirimleri kontrol edilemedi:', (e as Error).message)
    })
    .finally(() => {
      suankiStokKontrolu = null
    })
  return suankiStokKontrolu
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
