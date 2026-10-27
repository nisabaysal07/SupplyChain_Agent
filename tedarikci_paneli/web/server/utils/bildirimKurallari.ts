import type { BildirimTercihleri } from '../../shared/types/kullanici'
import type { BildirimTuru } from '../../shared/types/bildirim'
import type { KayitliOlay } from '../../shared/types/modelOlayi'
import type { Seviye } from '../../shared/types/veri'
import { olayAktifMi } from './risk'

// Model bir olay gönderdiğinde bildirim düşüp düşmeyeceğine ve ne yazacağına karar veren saf kurallar

const SIRA: Record<Seviye, number> = { yuksek: 0, orta: 1, dusuk: 2 }

export function bildirimTuruBul(onceki: KayitliOlay | null, yeni: KayitliOlay, bugun: string): BildirimTuru | null {
  // Bitmiş ya da henüz başlamamış olay için bildirim yok
  if (!olayAktifMi(yeni, bugun)) return null
  if (!onceki) return 'yeni_olay'
  // Var olan habere çıkarım ilk kez geldiyse ya da model çıkarımı yeniledi ise
  if (yeni.cikarim && yeni.cikarim.olusturma !== onceki.cikarim?.olusturma) return 'yeni_cikarim'
  // Haberin metni vb. düzeltildi: kullanıcıyı yeniden rahatsız etme
  return null
}

const ilkCumle = (metin: string) => {
  const cumle = metin.trim().split(/(?<=[.!?])\s+/)[0] ?? metin
  return cumle.length > 180 ? `${cumle.slice(0, 177)}…` : cumle
}

// Model çıkarımı varsa en önemli bulgusu (yoksa özetinin ilk cümlesi), yoksa haberin özeti
export function bildirimIcerigi(olay: KayitliOlay): { seviye: Seviye, mesaj: string } {
  const c = olay.cikarim
  if (!c) return { seviye: olay.siddet, mesaj: ilkCumle(olay.ozet) }
  const enOnemli = [...c.bulgular].sort((a, b) => SIRA[a.seviye] - SIRA[b.seviye])[0]
  return {
    seviye: c.genelDegerlendirme.seviye,
    mesaj: `Model: ${enOnemli ? enOnemli.baslik : ilkCumle(c.ozet)}`
  }
}

export function kullaniciIstiyorMu(tercih: BildirimTercihleri, seviye: Seviye): boolean {
  return tercih.uygulamaIci && tercih.seviyeler.includes(seviye)
}
