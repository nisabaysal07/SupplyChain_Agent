import type { Seviye } from './veri'

// yeni_olay: model yeni bir haber gönderdi · yeni_cikarim: var olan habere modelin çıkarımı geldi (veya yenilendi)
export type BildirimTuru = 'yeni_olay' | 'yeni_cikarim'

export interface Bildirim {
  id: string
  olayId: string
  tur: BildirimTuru
  // Çıkarım varsa modelin genel değerlendirmesi, yoksa haberin şiddeti
  seviye: Seviye
  baslik: string
  mesaj: string
  olusturma: string
  okundu: boolean
}

export interface BildirimListesi {
  okunmamis: number
  bildirimler: Bildirim[]
}
