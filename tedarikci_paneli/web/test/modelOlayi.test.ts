import { readdirSync, readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { anahtarDogruMu } from '../server/utils/modelErisimi'
import { kapsamUyarilari, ModelOlaySemasi } from '../shared/utils/modelOlayi'

const KLASOR = new URL('../ornek/olaylar/', import.meta.url)
const ORNEKLER = readdirSync(KLASOR).filter(d => d.endsWith('.json'))
  .map(d => JSON.parse(readFileSync(new URL(d, KLASOR), 'utf8')))
const MERSIN = ORNEKLER.find(o => o.id === 'ornek-2')

const gecerliMi = (degisiklik: Record<string, unknown>) => ModelOlaySemasi.safeParse({ ...MERSIN, ...degisiklik }).success

describe('model olayı şeması', () => {
  it('ornek/olaylar altındaki bütün örnekler geçerli', () => {
    expect(ORNEKLER).toHaveLength(6)
    for (const o of ORNEKLER) expect(ModelOlaySemasi.safeParse(o).success, o.id).toBe(true)
  })

  it('çıkarım isteğe bağlı; verilmezse olay yine geçerli', () => {
    const { cikarim: _c, ...cikarimsiz } = MERSIN
    expect(ModelOlaySemasi.safeParse(cikarimsiz).success).toBe(true)
  })

  it('varsayılanlar: gecikme yok, örnek değil, bitiş yok, kaynak bağlantısı yok', () => {
    const { gecikmeVar: _g, ornek: _o, bitisTarihi: _b, ...enAz } = MERSIN
    const r = ModelOlaySemasi.parse({ ...enAz, kaynak: { ad: 'Haber' } })
    expect([r.gecikmeVar, r.ornek, r.bitisTarihi, r.kaynak.url]).toEqual([false, false, null, null])
  })

  it('kapsam en az bir ölçüt içermeli', () => {
    expect(gecerliMi({ kapsam: {} })).toBe(false)
    expect(gecerliMi({ kapsam: { ulkeler: [] } })).toBe(false)
  })

  it('id, tarih, hs6 ve bağlantılar doğrulanır', () => {
    expect(gecerliMi({ id: '../kullanici/x' })).toBe(false)
    expect(gecerliMi({ tarih: '21.10.2026' })).toBe(false)
    expect(gecerliMi({ bitisTarihi: '2026-10-01' })).toBe(false)
    expect(gecerliMi({ kapsam: { hs6: ['8504'] } })).toBe(false)
    expect(gecerliMi({ kaynak: { ad: 'x', url: 'http://haber.com' } })).toBe(false)
    expect(gecerliMi({ kaynak: { ad: 'x', url: 'javascript:alert(1)' } })).toBe(false)
  })

  it('çıkarımdaki seviye, skor ve güven aralık dışında olamaz', () => {
    const c = MERSIN.cikarim
    expect(gecerliMi({ cikarim: { ...c, genelDegerlendirme: { seviye: 'kritik' } } })).toBe(false)
    expect(gecerliMi({ cikarim: { ...c, genelDegerlendirme: { seviye: 'orta', guven: 1.5 } } })).toBe(false)
    expect(gecerliMi({ cikarim: { ...c, olusturma: '24.10.2026' } })).toBe(false)
  })
})

describe('kapsam uyarıları', () => {
  const REFERANS = { ulkeler: ['Çin', 'Tayvan'], noktalar: ['Port of Mersin'], hs6: ['850440'], firmalar: ['ASUS'] }
  it('panelde olmayan adlar uyarı olarak döner', () => {
    expect(kapsamUyarilari({ ulkeler: ['Çin', 'China'], noktalar: ['Mersin Limanı'] }, REFERANS)).toEqual([
      'kapsam.ulkeler: "China" panelde tanımlı değil',
      'kapsam.noktalar: "Mersin Limanı" panelde tanımlı değil'
    ])
  })
  it('hepsi eşleşiyorsa uyarı yok', () => {
    expect(kapsamUyarilari({ ulkeler: ['Çin'], hs6: ['850440'] }, REFERANS)).toEqual([])
  })
})

describe('model erişim anahtarı', () => {
  const ANAHTAR = 'x'.repeat(40)
  it('yalnızca birebir aynı anahtar kabul edilir', () => {
    expect(anahtarDogruMu(ANAHTAR, ANAHTAR)).toBe(true)
    expect(anahtarDogruMu(`${ANAHTAR}y`, ANAHTAR)).toBe(false)
    expect(anahtarDogruMu(undefined, ANAHTAR)).toBe(false)
    expect(anahtarDogruMu('', '')).toBe(false)
  })
})
