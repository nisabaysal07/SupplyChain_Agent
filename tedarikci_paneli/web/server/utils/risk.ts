import type { Olay, OlayEtkisi, RiskBileseni, RiskSonucu, Seviye, Tedarikci } from '../../shared/types/veri'
import { seviyeBul } from '../../shared/utils/seviye'

// Kural tabanlı tedarikçi risk skoru (0–100). Açıklaması: web/RISK_MODELI.md
// Bu dosyadaki fonksiyonlar saftır: aynı girdiye her zaman aynı sonucu verir ("bugün" dışarıdan gelir).

const SIDDET_PUANI: Record<Seviye, number> = { dusuk: 5, orta: 15, yuksek: 25 }
const SIDDET_SIRASI: Record<Seviye, number> = { dusuk: 0, orta: 1, yuksek: 2 }
const GUN_MS = 86_400_000

const sinirla = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v))
const yuvarla = (v: number) => Math.round(v * 10) / 10
const yuzde = (v: number) => `%${Math.round(v * 100)}`

export function gunFarki(baslangic: string, bitis: string): number {
  return Math.round((Date.parse(bitis) - Date.parse(baslangic)) / GUN_MS)
}

export function kullanilabilirGun(t: Tedarikci): number {
  return t.stok.kullanilabilir / (t.yillikAdet / 365)
}

// Tarihler ISO (YYYY-AA-GG) olduğu için metin karşılaştırması tarih sırasını verir
export function olayAktifMi(o: Olay, bugun: string): boolean {
  return o.tarih <= bugun && (o.bitisTarihi === null || o.bitisTarihi >= bugun)
}

export function olayEslesir(o: Olay, t: Tedarikci): boolean {
  const { ulkeler, noktalar, hs6, firmalar } = o.kapsam
  const noktalarim = [t.rota.cikis, t.rota.aktarma, t.rota.varis].filter((n): n is string => n !== null)
  const kosullar: boolean[] = []
  if (ulkeler?.length) kosullar.push(ulkeler.includes(t.menseUlke))
  if (noktalar?.length) kosullar.push(noktalarim.some(n => noktalar.includes(n)))
  if (hs6?.length) kosullar.push(hs6.includes(t.hs6))
  if (firmalar?.length) kosullar.push(firmalar.includes(t.firma))
  return kosullar.length > 0 && kosullar.every(Boolean)
}

function stokBileseni(t: Tedarikci): RiskBileseni {
  const oran = t.stok.kullanilabilir / t.stok.siparisSeviyesi
  return {
    ad: 'Stok',
    enFazla: 30,
    // Oran 1,5 ve üstü → 0 puan; 0,5 ve altı → 30 puan; arası doğrusal
    puan: yuvarla(30 * sinirla(1.5 - oran, 0, 1)),
    aciklama: `Kullanılabilir stok sipariş seviyesinin ${yuzde(oran)}'i (${Math.round(kullanilabilirGun(t))} günlük)`
  }
}

function rotaBileseni(t: Tedarikci): RiskBileseni {
  return {
    ad: 'Rota',
    enFazla: 20,
    puan: yuvarla(20 * sinirla(t.rota.transitGun / 30, 0, 1)),
    aciklama: `${t.rota.mod === 'hava' ? 'Hava' : 'Deniz'} yolu, ${t.rota.transitGun} gün`
  }
}

function ticaretBileseni(t: Tedarikci): RiskBileseni {
  const vergi = t.vergi.gumrukVergisi + t.vergi.ilaveGumrukVergisi
  const nedenler = [
    t.anlasmaVar ? 'serbest ticaret anlaşması var' : 'serbest ticaret anlaşması yok',
    vergi > 0 ? `gümrük vergisi + İGV ${yuzde(vergi)}` : 'gümrük vergisi yok'
  ]
  return {
    ad: 'Ticaret',
    enFazla: 15,
    puan: (t.anlasmaVar ? 0 : 10) + (vergi > 0 ? 5 : 0),
    aciklama: `${t.menseUlke}: ${nedenler.join(', ')}`
  }
}

function sozlesmeBileseni(t: Tedarikci, bugun: string): RiskBileseni {
  const kalan = gunFarki(bugun, t.sozlesmeBitis)
  return {
    ad: 'Sözleşme',
    enFazla: 10,
    puan: kalan <= 30 ? 10 : kalan <= 90 ? 5 : 0,
    aciklama: kalan < 0 ? `Sözleşme ${-kalan} gün önce bitti` : `Sözleşmenin bitmesine ${kalan} gün var`
  }
}

function olayBileseni(eslesen: Olay[]): RiskBileseni {
  if (!eslesen.length) {
    return { ad: 'Olaylar', enFazla: 25, puan: 0, aciklama: 'Etkileyen aktif olay yok' }
  }
  // En ağır olayın puanı + diğer her olay için 5 puan, en fazla 25
  const enAgir = eslesen[0]!
  return {
    ad: 'Olaylar',
    enFazla: 25,
    puan: Math.min(25, SIDDET_PUANI[enAgir.siddet] + 5 * (eslesen.length - 1)),
    aciklama: `${eslesen.length} aktif olay; en ağırı: ${enAgir.baslik}`
  }
}

export function riskHesapla(t: Tedarikci, olaylar: Olay[], bugun: string): RiskSonucu {
  const eslesen = olaylar
    .filter(o => olayAktifMi(o, bugun) && olayEslesir(o, t))
    .sort((a, b) => SIDDET_SIRASI[b.siddet] - SIDDET_SIRASI[a.siddet])
  const bilesenler = [
    stokBileseni(t),
    rotaBileseni(t),
    ticaretBileseni(t),
    sozlesmeBileseni(t, bugun),
    olayBileseni(eslesen)
  ]
  const skor = Math.round(bilesenler.reduce((top, b) => top + b.puan, 0))
  return { skor, seviye: seviyeBul(skor), bilesenler, olayIdleri: eslesen.map(o => o.id) }
}

export function olayEtkisi(o: Olay, t: Tedarikci): OlayEtkisi {
  const gecikmeVar = o.gecikmeVar ?? false
  return {
    tedarikciId: t.id,
    firma: t.firma,
    parca: t.parca,
    maliyetEtkisiUsd: Math.round(t.yillikAlimUsd * (o.ekMaliyetOrani ?? 0)),
    gecikmeVar,
    // Gecikme süresi bilinmez: stok zaten yeniden sipariş seviyesinin altındaysa her gecikme stoğu tehdit eder
    stokYetmeyebilir: gecikmeVar && t.stok.durum === 'siparis_gerekli'
  }
}
