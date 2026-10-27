// Grafiklerin ortak tipleri ve renkleri (renk değerleri app/assets/css/main.css'te --viz-*)
import type { IpucuSatiri } from '~/composables/useIpucu'

export interface GrafikTablosu {
  basliklar: string[]
  satirlar: string[][]
}

export interface Dilim {
  ad: string
  deger: number
  renk: string
  ikon?: string
}

export interface Cubuk {
  ad: string
  deger: number
  etiket: string
  ayrinti?: IpucuSatiri[]
}

// Risk seviyesi bir durumdur: durum renkleri, her zaman ikon ve etiketle birlikte
export const SEVIYE_VIZ_RENGI: Record<Seviye, string> = {
  dusuk: 'var(--viz-iyi)',
  orta: 'var(--viz-uyari)',
  yuksek: 'var(--viz-kritik)'
}
