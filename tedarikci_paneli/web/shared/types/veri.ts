// Sunucu ile arayüz arasında paylaşılan veri tipleri

export type TasimaModu = 'deniz' | 'hava'

export type StokDurumu = 'yeterli' | 'siparis_gerekli'

export interface Rota {
  mod: TasimaModu
  cikis: string
  aktarma: string | null
  varis: string
  transitGun: number
}

export interface Stok {
  eldeki: number
  rezerve: number
  kullanilabilir: number
  siparisSeviyesi: number
  durum: StokDurumu
}

// Menşe ülkenin çarpanı uygulanmış oranlar (ör. anlaşmalı ülkede GV ve İGV 0)
export interface UygulananVergi {
  gumrukVergisi: number
  ilaveGumrukVergisi: number
}

export interface Tedarikci {
  id: number
  parca: string
  hs6: string
  gtip12: string
  firma: string
  firmaResmiAd: string
  menseUlke: string
  anlasmaVar: boolean
  vergi: UygulananVergi
  birlestirmeUlke: string
  fiyatUsd: number
  fiyatTarihi: string
  sozlesmeBaslangic: string
  sozlesmeBitis: string
  rota: Rota
  stok: Stok
  yillikAdet: number
  yillikAlimUsd: number
}

// ---------------------------------------------------------------------------
// Olaylar ve risk
// ---------------------------------------------------------------------------

export type OlayTuru = 'vergi' | 'grev' | 'liman' | 'dogal_afet' | 'jeopolitik' | 'fiyat'

export type Seviye = 'dusuk' | 'orta' | 'yuksek'

// Bir olayın hangi tedarikçileri etkilediği. Verilen ölçütlerin hepsi sağlanmalı
// (ölçüt içindeki listeden biri yeterli). Hiç ölçüt yoksa olay kimseyi etkilemez.
export interface OlayKapsami {
  ulkeler?: string[]
  noktalar?: string[]
  hs6?: string[]
  firmalar?: string[]
}

export interface Olay {
  id: string
  baslik: string
  ozet: string
  tur: OlayTuru
  siddet: Seviye
  tarih: string
  bitisTarihi: string | null
  kaynak: { ad: string, url: string | null }
  ornek: boolean
  kapsam: OlayKapsami
  ekMaliyetOrani?: number
  // Haberden gecikme süresi çıkarılamaz; yalnızca sevkiyatlarda gecikme beklenip beklenmediği
  gecikmeVar?: boolean
}

export interface RiskBileseni {
  ad: string
  puan: number
  enFazla: number
  aciklama: string
}

export interface RiskSonucu {
  skor: number
  seviye: Seviye
  bilesenler: RiskBileseni[]
  olayIdleri: string[]
}

export interface RiskliTedarikci extends Tedarikci {
  risk: RiskSonucu
}

export interface OlayEtkisi {
  tedarikciId: number
  firma: string
  parca: string
  maliyetEtkisiUsd: number
  gecikmeVar: boolean
  stokYetmeyebilir: boolean
}

export interface EtkiliOlay extends Olay {
  etkilenenler: OlayEtkisi[]
  toplamMaliyetEtkisiUsd: number
  // Model bu haber için çıkarım raporu gönderdi mi (rapor: /api/olaylar/<id>/analiz)
  analizVar: boolean
}
