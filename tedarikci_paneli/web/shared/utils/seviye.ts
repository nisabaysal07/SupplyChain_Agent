import type { Seviye } from '../types/veri'

// Risk skoru eşikleri: hem sunucu hem arayüz aynı kuralı kullanır.
// Not: Nuxt'un otomatik içe aktarma tarayıcısı (mlly), virgüllü nesneyle başlayan bir
// `export const`'tan sonraki dışa aktarmaları kaçırıyor; bu yüzden eşikler dışa aktarılmaz.
const RISK_ESIKLERI = { orta: 35, yuksek: 60 } as const

export function seviyeBul(skor: number): Seviye {
  if (skor >= RISK_ESIKLERI.yuksek) return 'yuksek'
  if (skor >= RISK_ESIKLERI.orta) return 'orta'
  return 'dusuk'
}
