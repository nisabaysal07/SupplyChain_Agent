import type { Olay, Tedarikci } from '../shared/types/veri'

export const BUGUN = '2026-10-23'

// Bellek tedarikçisinin (Kingston) CSV'deki değerleri
export function tedarikci(degisiklik: Partial<Tedarikci> = {}): Tedarikci {
  return {
    id: 3,
    parca: 'Bellek',
    hs6: '847330',
    gtip12: '847330200000',
    firma: 'Kingston',
    firmaResmiAd: 'Kingston Technology Company, Inc.',
    menseUlke: 'Tayvan',
    anlasmaVar: false,
    vergi: { gumrukVergisi: 0, ilaveGumrukVergisi: 0 },
    birlestirmeUlke: 'Tayvan',
    fiyatUsd: 635,
    fiyatTarihi: '2026-10-21',
    sozlesmeBaslangic: '2026-10-01',
    sozlesmeBitis: '2026-12-31',
    rota: { mod: 'hava', cikis: 'Taiwan Taoyuan International Airport', aktarma: null, varis: 'Istanbul Airport', transitGun: 1 },
    stok: { eldeki: 466, rezerve: 192, kullanilabilir: 274, siparisSeviyesi: 438, durum: 'siparis_gerekli' },
    yillikAdet: 10_000,
    yillikAlimUsd: 6_350_000,
    ...degisiklik
  }
}

export function olay(degisiklik: Partial<Olay> = {}): Olay {
  return {
    id: 'o1',
    baslik: 'Test olayı',
    ozet: '',
    tur: 'grev',
    siddet: 'orta',
    tarih: '2026-10-20',
    bitisTarihi: null,
    kaynak: { ad: 'test', url: null },
    ornek: true,
    kapsam: { ulkeler: ['Tayvan'] },
    ...degisiklik
  }
}
