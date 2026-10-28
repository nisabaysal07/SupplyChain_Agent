import { describe, expect, it } from 'vitest'
import { BildirimSemasi, GirisSemasi, guvenliYonlendirme, SifreSemasi, SistemSemasi } from '../shared/utils/semalar'

describe('giriş sonrası yönlendirme', () => {
  it('site içi yollara izin verir', () => {
    expect(guvenliYonlendirme('/olaylar?olay=ornek-1')).toBe('/olaylar?olay=ornek-1')
  })
  it('başka siteye yönlendirmeyi engeller', () => {
    for (const kotu of ['//kotu.site', '/\\kotu.site', 'https://kotu.site', 'javascript:alert(1)', '', undefined, ['/a']]) {
      expect(guvenliYonlendirme(kotu)).toBe('/')
    }
  })
})

describe('şemalar', () => {
  it('e-posta küçük harfe çevrilir ve boşluklar atılır', () => {
    expect(GirisSemasi.parse({ eposta: '  Yonetici@ChainGuard.TEST ', sifre: 'x' }).eposta).toBe('yonetici@chainguard.test')
  })
  it('yeni şifre en az 12 karakter, tekrar aynı ve eskisinden farklı olmalı', () => {
    const tamam = { mevcut: 'eski-sifre-123', yeni: 'yeni-uzun-sifre', tekrar: 'yeni-uzun-sifre' }
    expect(SifreSemasi.safeParse(tamam).success).toBe(true)
    expect(SifreSemasi.safeParse({ ...tamam, yeni: 'kisa', tekrar: 'kisa' }).success).toBe(false)
    expect(SifreSemasi.safeParse({ ...tamam, tekrar: 'farkli-sifre-1' }).success).toBe(false)
    expect(SifreSemasi.safeParse({ ...tamam, yeni: tamam.mevcut, tekrar: tamam.mevcut }).success).toBe(false)
  })
  it('bildirim seviyeleri ve senkronizasyon sıklığı yalnızca izin verilen değerleri alır', () => {
    expect(BildirimSemasi.safeParse({ eposta: true, uygulamaIci: false, seviyeler: ['kritik'] }).success).toBe(false)
    expect(SistemSemasi.safeParse({ senkronizasyonSaat: 2 }).success).toBe(false)
    expect(SistemSemasi.safeParse({ senkronizasyonSaat: 3 }).success).toBe(true)
    expect(SistemSemasi.safeParse({ senkronizasyonSaat: 24 }).success).toBe(true)
  })
})
