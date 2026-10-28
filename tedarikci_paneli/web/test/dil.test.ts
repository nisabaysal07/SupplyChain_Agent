import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import en from '../app/i18n/en'
import tr from '../app/i18n/tr'
import { bicimler } from '../shared/utils/bicim'

// Bulunamayan anahtar ekranda ham haliyle ("pano.riskHaritas") görünür; bu testler bunu derlemeden önce yakalar

function anahtarlar(o: object, onek = ''): string[] {
  return Object.entries(o).flatMap(([k, v]) =>
    v && typeof v === 'object' && !Array.isArray(v) ? anahtarlar(v, `${onek}${k}.`) : [`${onek}${k}`])
}

function dosyalar(dizin: string): string[] {
  return readdirSync(dizin).flatMap((ad) => {
    const yol = join(dizin, ad)
    return statSync(yol).isDirectory() ? dosyalar(yol) : /\.(vue|ts)$/.test(ad) ? [yol] : []
  })
}

const enAnahtarlari = new Set(anahtarlar(en))
const bul = (anahtar: string) => anahtar.split('.').reduce<unknown>((o, k) => (o as Record<string, unknown>)?.[k], en)

describe('arayüz sözlükleri', () => {
  it('Türkçe ve İngilizce aynı anahtarlara sahip', () => {
    expect(anahtarlar(tr).sort()).toEqual([...enAnahtarlari].sort())
  })

  it('koddaki her sabit t(\'...\') anahtarı sözlükte var', () => {
    const kok = join(__dirname, '..')
    const eksik: string[] = []
    for (const dosya of [...dosyalar(join(kok, 'app')), ...dosyalar(join(kok, 'shared'))]) {
      if (dosya.includes(`${join('app', 'i18n')}`)) continue
      const metin = readFileSync(dosya, 'utf-8')
      for (const [, anahtar] of metin.matchAll(/\bt\(\s*'([a-zA-Z_.]+)'/g)) {
        if (bul(anahtar!) === undefined) eksik.push(`${dosya}: ${anahtar}`)
      }
      // Şemalardaki doğrulama mesajları da sözlük anahtarıdır
      for (const [, anahtar] of metin.matchAll(/'(dogrulama\.[a-zA-Z]+)'/g)) {
        if (bul(anahtar!) === undefined) eksik.push(`${dosya}: ${anahtar}`)
      }
    }
    expect(eksik).toEqual([])
  })

  it('her olay türü, seviye ve risk bileşeninin iki dilde adı var', () => {
    for (const s of [en, tr]) {
      expect(Object.keys(s.olayTuru).sort()).toEqual(['dogal_afet', 'fiyat', 'grev', 'jeopolitik', 'liman', 'vergi'])
      expect(Object.keys(s.seviye).sort()).toEqual(['dusuk', 'orta', 'yuksek'])
      expect(Object.keys(s.risk.ad).sort()).toEqual(['olaylar', 'rota', 'sozlesme', 'stok', 'ticaret'])
    }
  })
})

describe('dile göre biçimler', () => {
  it('para ve yüzde seçili dilin kurallarıyla yazılır', () => {
    expect(bicimler('en').para(1234567)).toBe('$1,234,567')
    expect(bicimler('tr').para(1234567)).toMatch(/^\$1\.234\.567$|^1\.234\.567 \$$/)
    expect(bicimler('en').yuzde(0.042)).toBe('4.2%')
    expect(bicimler('tr').yuzde(0.042)).toBe('%4,2')
  })
  it('tarih ay adı seçili dilde', () => {
    expect(bicimler('en').tarih('2026-10-12')).toBe('Oct 12, 2026')
    expect(bicimler('tr').tarih('2026-10-12')).toBe('12 Eki 2026')
  })
})
