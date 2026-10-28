import { createStorage } from 'unstorage'
import { describe, expect, it } from 'vitest'
import { EN_FAZLA_HATA, girisKilidiOlustur, KILIT_SURESI_MS } from '../server/utils/girisKilidi'

function kur() {
  const depo = createStorage()
  let simdi = 1_000_000
  const kilit = girisKilidiOlustur(depo, () => simdi)
  return { depo, kilit, ilerlet: (ms: number) => { simdi += ms } }
}

// Giriş ucundaki gibi: önce deneme sayılır, şifre doğruysa sayaç sıfırlanır
async function dene(kilit: ReturnType<typeof girisKilidiOlustur>, eposta: string, dogru: boolean) {
  const izinli = await kilit.denemeBaslat(eposta)
  if (izinli && dogru) {
    await kilit.basarili(eposta)
    return 'giris'
  }
  return 'red'
}

describe('girisKilidi', () => {
  it('5 hatalı denemeden sonra doğru şifre de reddedilir', async () => {
    const { kilit } = kur()
    for (let i = 0; i < EN_FAZLA_HATA; i++) expect(await dene(kilit, 'a@ornek.com', false)).toBe('red')
    expect(await dene(kilit, 'a@ornek.com', true)).toBe('red')
  })

  it('kilit 15 dakika sürer, sonra doğru şifre kabul edilir', async () => {
    const { kilit, ilerlet } = kur()
    for (let i = 0; i < EN_FAZLA_HATA; i++) await dene(kilit, 'a@ornek.com', false)
    ilerlet(KILIT_SURESI_MS - 1)
    expect(await dene(kilit, 'a@ornek.com', true)).toBe('red')
    ilerlet(1)
    expect(await dene(kilit, 'a@ornek.com', true)).toBe('giris')
  })

  it('kilitliyken yapılan denemeler kilidi uzatmaz', async () => {
    const { kilit, ilerlet } = kur()
    for (let i = 0; i < EN_FAZLA_HATA; i++) await dene(kilit, 'a@ornek.com', false)
    for (let i = 0; i < 20; i++) {
      ilerlet(KILIT_SURESI_MS / 40)
      await dene(kilit, 'a@ornek.com', false)
    }
    ilerlet(KILIT_SURESI_MS / 2)
    expect(await dene(kilit, 'a@ornek.com', true)).toBe('giris')
  })

  it('başarılı giriş sayacı sıfırlar', async () => {
    const { kilit } = kur()
    for (let i = 0; i < EN_FAZLA_HATA - 1; i++) await dene(kilit, 'a@ornek.com', false)
    expect(await dene(kilit, 'a@ornek.com', true)).toBe('giris')
    // Sıfırlanmasaydı bir sonraki hata kilitlerdi
    for (let i = 0; i < EN_FAZLA_HATA - 1; i++) await dene(kilit, 'a@ornek.com', false)
    expect(await dene(kilit, 'a@ornek.com', true)).toBe('giris')
  })

  it('5. denemede doğru şifre girilirse giriş yapılır', async () => {
    const { kilit } = kur()
    for (let i = 0; i < EN_FAZLA_HATA - 1; i++) await dene(kilit, 'a@ornek.com', false)
    expect(await dene(kilit, 'a@ornek.com', true)).toBe('giris')
  })

  it('15 dakikadan eski hatalar sayılmaz', async () => {
    const { kilit, ilerlet } = kur()
    for (let i = 0; i < EN_FAZLA_HATA - 1; i++) await dene(kilit, 'a@ornek.com', false)
    ilerlet(KILIT_SURESI_MS)
    await dene(kilit, 'a@ornek.com', false)
    expect(await dene(kilit, 'a@ornek.com', true)).toBe('giris')
  })

  it('e-postalar birbirini etkilemez; kayıtsız e-posta da kilitlenir', async () => {
    const { kilit } = kur()
    for (let i = 0; i < EN_FAZLA_HATA; i++) await dene(kilit, 'kayitsiz@ornek.com', false)
    expect(await kilit.denemeBaslat('kayitsiz@ornek.com')).toBe(false)
    expect(await dene(kilit, 'b@ornek.com', true)).toBe('giris')
  })

  it('aynı anda gönderilen denemeler sınırı aşamaz', async () => {
    const { kilit } = kur()
    const sonuclar = await Promise.all(Array.from({ length: 50 }, () => kilit.denemeBaslat('a@ornek.com')))
    expect(sonuclar.filter(Boolean)).toHaveLength(EN_FAZLA_HATA)
  })

  it('e-posta depoda açık yazılmaz', async () => {
    const { depo, kilit } = kur()
    await kilit.denemeBaslat('a@ornek.com')
    const anahtarlar = await depo.getKeys()
    expect(anahtarlar).toHaveLength(1)
    expect(anahtarlar[0]).not.toContain('ornek')
  })
})
