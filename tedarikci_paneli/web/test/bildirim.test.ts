import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import type { KayitliOlay } from '../shared/types/modelOlayi'
import { ModelOlaySemasi } from '../shared/utils/modelOlayi'
import { bildirimIcerigi, bildirimTuruBul, kullaniciIstiyorMu, stokBildirimIcerigi, yeniSiparisGerekenler } from '../server/utils/bildirimKurallari'
import { tedarikci } from './ornekler'

const BUGUN = '2026-10-24'
const oku = (id: string): KayitliOlay => ({
  ...ModelOlaySemasi.parse(JSON.parse(readFileSync(new URL(`../ornek/olaylar/${id}.json`, import.meta.url), 'utf8'))),
  alinma: '2026-10-24T10:00:00Z'
})
const MERSIN = oku('ornek-2') // çıkarımlı
const { cikarim: _c, ...cikarimsizMersin } = MERSIN
const MERSIN_CIKARIMSIZ: KayitliOlay = cikarimsizMersin

describe('ne zaman bildirim düşer', () => {
  it('yeni haber gelince', () => {
    expect(bildirimTuruBul(null, MERSIN_CIKARIMSIZ, BUGUN)).toBe('yeni_olay')
  })
  it('var olan habere çıkarım ilk kez gelince', () => {
    expect(bildirimTuruBul(MERSIN_CIKARIMSIZ, MERSIN, BUGUN)).toBe('yeni_cikarim')
  })
  it('model çıkarımı yenileyince', () => {
    const yeni = { ...MERSIN, cikarim: { ...MERSIN.cikarim!, olusturma: '2026-10-25T09:00:00+03:00' } }
    expect(bildirimTuruBul(MERSIN, yeni, BUGUN)).toBe('yeni_cikarim')
  })
  it('aynı olay aynı çıkarımla tekrar gelince bildirim yok', () => {
    expect(bildirimTuruBul(MERSIN, { ...MERSIN, ozet: 'düzeltilmiş özet' }, BUGUN)).toBeNull()
  })
  it('bitmiş olay için bildirim yok', () => {
    expect(bildirimTuruBul(null, oku('ornek-6'), BUGUN)).toBeNull()
  })
})

describe('bildirimde ne yazar', () => {
  it('çıkarım varsa: modelin genel değerlendirmesi ve en önemli bulgusu', () => {
    expect(bildirimIcerigi(MERSIN)).toEqual({ seviye: 'orta', mesaj: 'Model: Ekran kartında stok tükenme riski' })
  })
  it('çıkarım yoksa: haberin şiddeti ve özetinin ilk cümlesi', () => {
    const vergi = oku('ornek-1')
    expect(bildirimIcerigi(vergi).seviye).toBe('yuksek')
    expect(bildirimIcerigi(vergi).mesaj).toBe(vergi.ozet)
  })
})

describe('kullanıcı tercihleri', () => {
  const tercih = { eposta: true, uygulamaIci: true, seviyeler: ['yuksek' as const] }
  it('yalnızca seçtiği seviyeler', () => {
    expect(kullaniciIstiyorMu(tercih, 'yuksek')).toBe(true)
    expect(kullaniciIstiyorMu(tercih, 'orta')).toBe(false)
  })
  it('uygulama içi kapalıysa hiç', () => {
    expect(kullaniciIstiyorMu({ ...tercih, uygulamaIci: false }, 'yuksek')).toBe(false)
  })
})

describe('stok bildirimi', () => {
  const yeterli = tedarikci({ id: 1, stok: { eldeki: 900, rezerve: 0, kullanilabilir: 900, siparisSeviyesi: 438, durum: 'yeterli' } })
  const dusen = tedarikci({ id: 3 }) // 274 / 438
  it('parça sipariş seviyesinin altına ilk düştüğünde', () => {
    expect(yeniSiparisGerekenler([], [yeterli, dusen]).map(t => t.id)).toEqual([3])
  })
  it('önceki kontrolde de altındaysa tekrar bildirim yok', () => {
    expect(yeniSiparisGerekenler([3], [yeterli, dusen])).toEqual([])
  })
  it('toparlanıp yeniden düşerse yine bildirilir', () => {
    // Toparlanınca listeden çıkar (bir sonraki kontrolün öncekisi boştur)
    expect(yeniSiparisGerekenler([], [dusen]).map(t => t.id)).toEqual([3])
  })
  it('seviye: sipariş seviyesinin yarısı veya altı yüksek, değilse orta', () => {
    expect(stokBildirimIcerigi(dusen)).toEqual({
      seviye: 'orta',
      baslik: 'Kingston – Bellek',
      mesaj: 'Kullanılabilir stok 274, sipariş seviyesi 438'
    })
    const kritik = tedarikci({ stok: { eldeki: 200, rezerve: 0, kullanilabilir: 200, siparisSeviyesi: 438, durum: 'siparis_gerekli' } })
    expect(stokBildirimIcerigi(kritik).seviye).toBe('yuksek')
  })
})
