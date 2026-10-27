import type { OlayTuru, Seviye } from '../types/veri'

// Ekranlarda ve raporlarda aynı adların kullanılması için tek yer.
// Dışa aktarım sonda topluca yapılır: Nuxt'un otomatik içe aktarma tarayıcısı (mlly),
// virgüllü nesneyle başlayan bir `export const`'tan sonraki dışa aktarmaları kaçırıyor.

const SEVIYE_ETIKETI: Record<Seviye, string> = { dusuk: 'Düşük', orta: 'Orta', yuksek: 'Yüksek' }

const OLAY_TURU: Record<OlayTuru, { etiket: string, icon: string }> = {
  vergi: { etiket: 'Vergi', icon: 'i-lucide-landmark' },
  grev: { etiket: 'Grev', icon: 'i-lucide-hand' },
  liman: { etiket: 'Liman', icon: 'i-lucide-anchor' },
  dogal_afet: { etiket: 'Doğal afet', icon: 'i-lucide-cloud-lightning' },
  jeopolitik: { etiket: 'Jeopolitik', icon: 'i-lucide-globe' },
  fiyat: { etiket: 'Fiyat', icon: 'i-lucide-trending-up' }
}

export { OLAY_TURU, SEVIYE_ETIKETI }
