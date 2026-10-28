import { describe, expect, it } from 'vitest'
import type { Olay, Tedarikci } from '../shared/types/veri'
import { gunFarki, olayAktifMi, olayEslesir, olayEtkisi, riskHesapla } from '../server/utils/risk'
import { seviyeBul } from '../shared/utils/seviye'
import { BUGUN, olay, tedarikci } from './ornekler'

const bilesen = (t: Tedarikci, ad: string, olaylar: Olay[] = []) =>
  riskHesapla(t, olaylar, BUGUN).bilesenler.find(b => b.ad === ad)!.puan

describe('seviye eşikleri', () => {
  it('0–34 düşük, 35–59 orta, 60+ yüksek', () => {
    expect([0, 34, 35, 59, 60, 100].map(seviyeBul)).toEqual(['dusuk', 'dusuk', 'orta', 'orta', 'yuksek', 'yuksek'])
  })
})

describe('stok bileşeni', () => {
  it('sipariş seviyesinin 1,5 katı ve üstünde 0 puan', () => {
    expect(bilesen(tedarikci({ stok: { ...tedarikci().stok, kullanilabilir: 657 } }), 'Stok')).toBe(0)
  })
  it('sipariş seviyesinin yarısı ve altında 30 puan', () => {
    expect(bilesen(tedarikci({ stok: { ...tedarikci().stok, kullanilabilir: 100 } }), 'Stok')).toBe(30)
  })
  it('arada doğrusal: Bellek 274/438 → 26,2', () => {
    expect(bilesen(tedarikci(), 'Stok')).toBe(26.2)
  })
})

describe('diğer bileşenler', () => {
  it('rota: 30 gün ve üstü 20 puan, 1 gün 0,7', () => {
    expect(bilesen(tedarikci(), 'Rota')).toBe(0.7)
    expect(bilesen(tedarikci({ rota: { ...tedarikci().rota, transitGun: 45 } }), 'Rota')).toBe(20)
  })
  it('ticaret: anlaşma yoksa 10, vergi varsa +5, anlaşmalı ve vergisizse 0', () => {
    expect(bilesen(tedarikci(), 'Ticaret')).toBe(10)
    expect(bilesen(tedarikci({ vergi: { gumrukVergisi: 0.033, ilaveGumrukVergisi: 0.11 } }), 'Ticaret')).toBe(15)
    expect(bilesen(tedarikci({ anlasmaVar: true }), 'Ticaret')).toBe(0)
  })
  it('sözleşme: 30 gün ve altı 10, 90 gün ve altı 5, fazlası 0', () => {
    expect(bilesen(tedarikci({ sozlesmeBitis: '2026-11-10' }), 'Sözleşme')).toBe(10)
    expect(bilesen(tedarikci(), 'Sözleşme')).toBe(5)
    expect(bilesen(tedarikci({ sozlesmeBitis: '2027-06-30' }), 'Sözleşme')).toBe(0)
  })
})

describe('olay eşleşmesi', () => {
  it('ölçütlerin hepsi sağlanmalı', () => {
    const t = tedarikci()
    expect(olayEslesir(olay({ kapsam: { ulkeler: ['Tayvan'], hs6: ['847330'] } }), t)).toBe(true)
    expect(olayEslesir(olay({ kapsam: { ulkeler: ['Tayvan'], hs6: ['850440'] } }), t)).toBe(false)
  })
  it('rota noktalarından biri yeterli', () => {
    expect(olayEslesir(olay({ kapsam: { noktalar: ['Istanbul Airport'] } }), tedarikci())).toBe(true)
  })
  it('ölçütsüz olay kimseyi etkilemez', () => {
    expect(olayEslesir(olay({ kapsam: {} }), tedarikci())).toBe(false)
  })
  it('bitmiş ve henüz başlamamış olaylar aktif değil', () => {
    expect(olayAktifMi(olay({ bitisTarihi: '2026-10-22' }), BUGUN)).toBe(false)
    expect(olayAktifMi(olay({ tarih: '2026-10-24' }), BUGUN)).toBe(false)
    expect(olayAktifMi(olay({ bitisTarihi: BUGUN }), BUGUN)).toBe(true)
  })
})

describe('olay bileşeni', () => {
  it('en ağır olay + diğer her olay için 5, en fazla 25', () => {
    const t = tedarikci()
    expect(bilesen(t, 'Olaylar', [olay({ siddet: 'orta' })])).toBe(15)
    expect(bilesen(t, 'Olaylar', [olay({ siddet: 'dusuk' }), olay({ id: 'o2', siddet: 'orta' })])).toBe(20)
    expect(bilesen(t, 'Olaylar', [olay({ siddet: 'yuksek' }), olay({ id: 'o2' })])).toBe(25)
  })
  it('kapanmış olay skora katılmaz', () => {
    expect(bilesen(tedarikci(), 'Olaylar', [olay({ bitisTarihi: '2026-09-01' })])).toBe(0)
  })
})

describe('toplam skor', () => {
  it('Bellek, olaysız: 26,2 + 0,7 + 10 + 5 = 42 → orta', () => {
    const r = riskHesapla(tedarikci(), [], BUGUN)
    expect(r.skor).toBe(42)
    expect(r.seviye).toBe('orta')
  })
})

describe('olay etkisi', () => {
  it('ek maliyet yıllık alım × oran', () => {
    expect(olayEtkisi(olay({ ekMaliyetOrani: 0.08 }), tedarikci()).maliyetEtkisiUsd).toBe(508_000)
  })
  it('gecikme varken stok zaten sipariş seviyesinin altındaysa uyarır', () => {
    // Bellek: stok zaten sipariş seviyesinin altında → gecikme varsa stok yetmeyebilir
    expect(olayEtkisi(olay({ gecikmeVar: true }), tedarikci()).stokYetmeyebilir).toBe(true)
    expect(olayEtkisi(olay({ gecikmeVar: false }), tedarikci()).stokYetmeyebilir).toBe(false)
    expect(olayEtkisi(olay(), tedarikci()).gecikmeVar).toBe(false)
    const yeterli = tedarikci({ stok: { ...tedarikci().stok, kullanilabilir: 900, durum: 'yeterli' } })
    expect(olayEtkisi(olay({ gecikmeVar: true }), yeterli).stokYetmeyebilir).toBe(false)
  })
})

it('gunFarki', () => {
  expect(gunFarki('2026-10-23', '2026-12-31')).toBe(69)
})
