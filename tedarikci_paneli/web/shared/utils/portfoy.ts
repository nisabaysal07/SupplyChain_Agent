import type { RiskliTedarikci } from '../types/veri'

// Yıllık alım tutarıyla ağırlıklı ortalama: büyük alım yapılan tedarikçinin riski daha çok sayılır
export function portfoySkoru(liste: RiskliTedarikci[]): number {
  const toplamAlim = liste.reduce((t, x) => t + x.yillikAlimUsd, 0)
  if (!toplamAlim) return 0
  return Math.round(liste.reduce((t, x) => t + x.risk.skor * x.yillikAlimUsd, 0) / toplamAlim)
}
