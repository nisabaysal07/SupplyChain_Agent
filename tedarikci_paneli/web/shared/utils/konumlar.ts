// Harita konumları veritabanından gelir (locations.latitude / longitude / city, bkz. /api/konumlar).
// Burada yalnızca görünüm ayarları durur.

type EtiketYonu = 'sag' | 'sol' | 'ust' | 'alt'

// Bölge etiketinin daireye göre yeri; komşu bölgelerin etiketleri üst üste binmesin diye. Listede olmayan bölge sağa yazılır.
const ETIKET_YONLERI: Record<string, EtiketYonu> = {
  'Shenzhen': 'sol',
  'Kaohsiung': 'alt',
  'Ho Chi Minh': 'alt',
  'Mersin': 'alt',
  'İstanbul': 'ust'
}

// Ülke adı → world-atlas'taki ISO 3166 sayısal kod (haritada menşe ülkeyi vurgulamak için)
const ULKE_KODLARI: Record<string, string> = {
  'Güney Kore': '410',
  'Tayvan': '158',
  'Çin': '156',
  'Vietnam': '704',
  'Türkiye': '792'
}

export { ETIKET_YONLERI, ULKE_KODLARI }
export type { EtiketYonu }
