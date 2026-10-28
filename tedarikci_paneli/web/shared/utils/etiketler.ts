import type { OlayTuru } from '../types/veri'

// Olay türlerinin ikonları; adları arayüz dilinde: t(`olayTuru.${tur}`) (app/i18n).
// Dışa aktarım sonda topluca yapılır: Nuxt'un otomatik içe aktarma tarayıcısı (mlly),
// virgüllü nesneyle başlayan bir `export const`'tan sonraki dışa aktarmaları kaçırıyor.

const OLAY_TURU_IKONU: Record<OlayTuru, string> = {
  vergi: 'i-lucide-landmark',
  grev: 'i-lucide-hand',
  liman: 'i-lucide-anchor',
  dogal_afet: 'i-lucide-cloud-lightning',
  jeopolitik: 'i-lucide-globe',
  fiyat: 'i-lucide-trending-up'
}

export { OLAY_TURU_IKONU }
