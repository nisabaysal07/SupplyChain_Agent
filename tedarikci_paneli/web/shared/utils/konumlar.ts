// Haritada kullanılan konumlar. Anahtar, rotalar tablosundaki resmi addır (CSV / PostgreSQL ile birebir).
// Yakın limanlar aynı "bolge"de toplanır: haritada tek daire olarak görünürler.
// Tabloya yeni bir liman eklenirse buraya da eklenmeli; konumu bilinmeyen nokta haritada gösterilmez
// (Kontrol Paneli'nde "konumu bilinmeyen" olarak belirtilir).

interface Konum {
  enlem: number
  boylam: number
  bolge: string
  etiketYonu: 'sag' | 'sol' | 'ust' | 'alt'
}

const NOKTALAR: Record<string, Konum> = {
  'Port of Ningbo-Zhoushan': { enlem: 29.93, boylam: 121.85, bolge: 'Ningbo', etiketYonu: 'sag' },
  'Port of Shekou (Shenzhen)': { enlem: 22.48, boylam: 113.91, bolge: 'Shenzhen', etiketYonu: 'sol' },
  'Port of Yantian (Shenzhen)': { enlem: 22.57, boylam: 114.27, bolge: 'Shenzhen', etiketYonu: 'sol' },
  'Port of Kaohsiung': { enlem: 22.61, boylam: 120.28, bolge: 'Kaohsiung', etiketYonu: 'alt' },
  'Taiwan Taoyuan International Airport': { enlem: 25.08, boylam: 121.23, bolge: 'Taoyuan', etiketYonu: 'sag' },
  'Incheon International Airport': { enlem: 37.46, boylam: 126.44, bolge: 'Incheon', etiketYonu: 'sag' },
  'Tan Son Nhat International Airport': { enlem: 10.82, boylam: 106.65, bolge: 'Ho Chi Minh', etiketYonu: 'alt' },
  'Cai Mep Port': { enlem: 10.53, boylam: 107.03, bolge: 'Ho Chi Minh', etiketYonu: 'alt' },
  'Port of Mersin': { enlem: 36.79, boylam: 34.63, bolge: 'Mersin', etiketYonu: 'alt' },
  'Istanbul Airport': { enlem: 41.28, boylam: 28.75, bolge: 'İstanbul', etiketYonu: 'ust' }
}

// Ülke adı → world-atlas'taki ISO 3166 sayısal kod (haritada menşe ülkeyi vurgulamak için)
const ULKE_KODLARI: Record<string, string> = {
  'Güney Kore': '410',
  'Tayvan': '158',
  'Çin': '156',
  'Vietnam': '704',
  'Türkiye': '792'
}

export { NOKTALAR, ULKE_KODLARI }
export type { Konum }
