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

export type TaramaAraligi = 1 | 3 | 6 | 12 | 24

export interface SistemAyarlari {
  // Haber taramasının kaç saatte bir yapılacağı; main.py --schedule bunu supply_db.app_settings'ten okur
  senkronizasyonSaat: TaramaAraligi
}

export type TaramaDurumu = 'running' | 'success' | 'failed'

export interface SistemDurumu extends SistemAyarlari {
  // Taramanın ve panelin kullandığı anahtarlar. Anahtarların kendisi asla gönderilmez; yalnızca tanımlı olup olmadıkları
  anahtarlar: { tavily: boolean, nebius: boolean, modelErisimi: boolean, bildirimKanallari: boolean }
  // scan_logs'taki en son tarama; veritabanı yoksa veya hiç tarama yapılmadıysa null
  sonTarama: { baslangic: string, durum: TaramaDurumu, otomatik: boolean } | null
  // Tedarikçi verisinin kaynağı; bağlantı bilgisi gönderilmez
  veriKaynagi: { tur: 'postgresql' | 'yok', durum: 'bagli' | 'hata' | 'kapali' }
}
