import type { Seviye } from './veri'

// yeni_olay: model yeni bir haber gönderdi · yeni_cikarim: var olan habere modelin çıkarımı geldi (veya yenilendi)
// siparis_gerekli: bir parçanın kullanılabilir stoğu sipariş seviyesinin altına düştü
export type BildirimTuru = 'yeni_olay' | 'yeni_cikarim' | 'siparis_gerekli'

export interface StokBildirimi {
  tedarikciId: number
  kullanilabilir: number
  siparisSeviyesi: number
}

export interface Bildirim {
  id: string
  // Olay bildirimlerinde olayın, stok bildirimlerinde boş
  olayId?: string
  stok?: StokBildirimi
  tur: BildirimTuru
  // Çıkarım varsa modelin genel değerlendirmesi, yoksa haberin şiddeti; stokta sipariş seviyesine oranı
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
