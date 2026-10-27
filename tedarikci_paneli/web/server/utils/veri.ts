import type { Satir } from './csv'
import type { Tablolar } from './veriKaynagi'

// Tedarikçi verisi PostgreSQL'den (NUXT_DATABASE_URL tanımlıysa) ya da build_dataset.py'nin ürettiği
// CSV'lerden okunur. İki kaynak aynı tabloları verir; birleştirme kodu ortaktır.

// sirket.md: yılda 10.000 bilgisayar; ekran kartı ve monitör modellerin yarısında (5.000)
const YARIM_URETIMDEKI_PARCALAR = new Set(['Ekran kartı', 'Monitör'])
const YILLIK_URETIM = 10_000

function indeksle(rows: Satir[], anahtar: string): Map<string, Satir> {
  return new Map(rows.map(r => [r[anahtar]!, r]))
}

export function tedarikcileriBirlestir(t: Tablolar): Tedarikci[] {
  const rota = indeksle(t.rotalar, 'tedarikci_id')
  const parca = indeksle(t.parcalar, 'parca_id')
  const ulke = indeksle(t.ulkeler, 'ulke_id')
  const firma = indeksle(t.firmalar, 'firma_id')

  return t.tedarikciler.map((ted) => {
    const r = rota.get(ted.tedarikci_id!)
    const p = parca.get(ted.parca_id!)
    const u = ulke.get(ted.mense_ulke_id!)
    const f = firma.get(ted.firma_id!)
    if (!r || !p || !u || !f) {
      throw new Error(`Tedarikçi ${ted.tedarikci_id}: bağlantı eksik`)
    }

    const eldeki = Number(p.eldeki_stok)
    const rezerve = Number(p.rezerve_stok)
    const siparisSeviyesi = Number(p.yeniden_siparis_seviyesi)
    const kullanilabilir = eldeki - rezerve
    const fiyatUsd = Number(ted.perakende_usd)
    const yillikAdet = YARIM_URETIMDEKI_PARCALAR.has(p.parca_adi!) ? YILLIK_URETIM / 2 : YILLIK_URETIM

    return {
      id: Number(ted.tedarikci_id),
      parca: p.parca_adi!,
      hs6: p.hs6!,
      gtip12: p.gtip12!,
      firma: f.firma_adi!,
      firmaResmiAd: f.resmi_ad!,
      menseUlke: u.ulke_adi!,
      anlasmaVar: u.anlasma_durumu === '1',
      vergi: {
        gumrukVergisi: Number(p.tarife_gv_tercihsiz) * Number(u.gv_carpani),
        ilaveGumrukVergisi: Number(p.tarife_igv_tercihsiz) * Number(u.igv_carpani)
      },
      birlestirmeUlke: ted.birlestirme_ulke!,
      fiyatUsd,
      fiyatTarihi: ted.fiyat_tarihi!,
      sozlesmeBaslangic: ted.sozlesme_baslangic!,
      sozlesmeBitis: ted.sozlesme_bitis!,
      rota: {
        mod: r.tasima_modu as TasimaModu,
        cikis: r.cikis_noktasi!,
        aktarma: r.aktarma_noktasi === 'Aktarma yok' ? null : r.aktarma_noktasi!,
        varis: r.varis_noktasi!,
        transitGun: Number(r.transit_gun)
      },
      stok: {
        eldeki,
        rezerve,
        kullanilabilir,
        siparisSeviyesi,
        durum: kullanilabilir < siparisSeviyesi ? 'siparis_gerekli' : 'yeterli'
      },
      yillikAdet,
      yillikAlimUsd: Math.round(fiyatUsd * yillikAdet)
    }
  })
}

export async function tedarikcileriOku(): Promise<Tedarikci[]> {
  const havuz = veritabaniHavuzu()
  let tablolar: Tablolar
  try {
    tablolar = havuz ? await postgresTablolariniOku(havuz) : await csvTablolariniOku(useRuntimeConfig().veriKlasoru)
  }
  catch (e) {
    // Bağlantı ayrıntısı (sunucu adı, kullanıcı) tarayıcıya gönderilmez, yalnızca sunucu günlüğüne yazılır
    console.error('[ChainGuard] Tedarikçi verisi okunamadı:', (e as Error).message)
    throw createError({ statusCode: 503, statusMessage: havuz ? 'Veritabanına ulaşılamadı' : 'Veri dosyaları okunamadı' })
  }
  try {
    return tedarikcileriBirlestir(tablolar)
  }
  catch (e) {
    throw createError({ statusCode: 500, statusMessage: (e as Error).message })
  }
}
