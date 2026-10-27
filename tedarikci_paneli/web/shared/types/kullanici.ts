import type { Seviye } from './veri'

export type Rol = 'yonetici' | 'izleyici'

export interface BildirimTercihleri {
  eposta: boolean
  uygulamaIci: boolean
  seviyeler: Seviye[]
}

// Tarayıcıya gönderilebilen kullanıcı bilgisi (şifre özeti yok)
export interface Kullanici {
  id: string
  ad: string
  soyad: string
  eposta: string
  rol: Rol
  bildirimler: BildirimTercihleri
}

export interface SistemAyarlari {
  senkronizasyonSaat: 6 | 12 | 24
}

export interface SistemDurumu extends SistemAyarlari {
  // Anahtarların kendisi asla gönderilmez; yalnızca tanımlı olup olmadıkları
  anahtarlar: { tavily: boolean, nemotron: boolean }
  // Tedarikçi verisinin kaynağı; bağlantı bilgisi gönderilmez
  veriKaynagi: { tur: 'postgresql' | 'csv', durum: 'bagli' | 'hata' | 'kapali' }
}
