import { readFile } from 'node:fs/promises'
import { join } from 'node:path'
import type { Pool } from 'pg'
import { csvAyristir, type Satir } from './csv.ts'

// Tedarikçi verisinin iki kaynağı: PostgreSQL (NUXT_DATABASE_URL tanımlıysa) veya CSV dosyaları.
// İkisi de aynı tablo ve sütun adlarını kullanır (build_dataset.py, db/sema.sql).
// Tablo ve sütun adları bu sabit listeden gelir; kullanıcı girdisi SQL'e veya dosya yoluna hiç karışmaz.
// Not: Bu dosya db/yukle.ts tarafından Node ile doğrudan çalıştırıldığı için içe aktarmalar .ts uzantılıdır.

const SUTUNLAR = {
  ulkeler: ['ulke_id', 'ulke_adi', 'anlasma_durumu', 'gv_carpani', 'igv_carpani'],
  firmalar: ['firma_id', 'firma_adi', 'resmi_ad', 'merkez_ulke'],
  parcalar: ['parca_id', 'parca_adi', 'hs6', 'gtip12', 'tarife_gv_tercihsiz', 'tarife_igv_tercihsiz',
    'kultur_fonu_orani', 'otv_orani', 'kdv_orani', 'oran_kaynagi', 'eldeki_stok', 'rezerve_stok', 'yeniden_siparis_seviyesi'],
  tedarikciler: ['tedarikci_id', 'parca_id', 'firma_id', 'mense_ulke_id', 'birlestirme_ulke', 'perakende_usd',
    'fiyat_tarihi', 'sozlesme_baslangic', 'sozlesme_bitis'],
  rotalar: ['tedarikci_id', 'tasima_modu', 'cikis_noktasi', 'aktarma_noktasi', 'varis_noktasi', 'transit_gun']
} as const

type TabloAdi = keyof typeof SUTUNLAR
type Tablolar = Record<TabloAdi, Satir[]>

// Yabancı anahtar sırasına göre: önce bağlanılan tablolar
const TABLO_SIRASI: TabloAdi[] = ['ulkeler', 'firmalar', 'parcalar', 'tedarikciler', 'rotalar']

async function csvTablolariniOku(klasor: string): Promise<Tablolar> {
  const okunan = await Promise.all(TABLO_SIRASI.map(async ad =>
    [ad, csvAyristir(await readFile(join(klasor, `${ad}.csv`), 'utf8'))] as const))
  return Object.fromEntries(okunan) as Tablolar
}

// Sayılar ve tarihler metne çevrilir: birleştirme kodu iki kaynakta da aynı biçimi görür
function metneCevir(deger: unknown): string {
  return deger === null || deger === undefined ? '' : String(deger)
}

async function postgresTablolariniOku(havuz: Pool): Promise<Tablolar> {
  const okunan = await Promise.all(TABLO_SIRASI.map(async (ad) => {
    const sutunlar = SUTUNLAR[ad]
    const { rows } = await havuz.query(`SELECT ${sutunlar.join(', ')} FROM ${ad} ORDER BY ${sutunlar[0]}`)
    const satirlar = rows.map((r: Record<string, unknown>) =>
      Object.fromEntries(sutunlar.map(s => [s, metneCevir(r[s])])))
    return [ad, satirlar] as const
  }))
  return Object.fromEntries(okunan) as Tablolar
}

export { csvTablolariniOku, postgresTablolariniOku, SUTUNLAR, TABLO_SIRASI }
export type { TabloAdi, Tablolar }
