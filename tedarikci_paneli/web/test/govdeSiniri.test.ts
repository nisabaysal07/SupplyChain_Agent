import { createServer, request, type Server } from 'node:http'
import type { AddressInfo } from 'node:net'
import { createApp, createRouter, defineEventHandler, readBody, readMultipartFormData, toNodeListener } from 'h3'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { govdeSiniri, govdeyiSinirliOku, type GuvenlikAyari } from '../server/utils/govdeSiniri'

// nuxt.config.ts ile aynı ayarlar
const GENEL: GuvenlikAyari = { requestSizeLimiter: { maxRequestSizeInBytes: 2_000_000, maxUploadFileRequestInBytes: 5_000_000 } }
const KAPANIS_MS = 300
const MODEL: GuvenlikAyari = { requestSizeLimiter: { maxRequestSizeInBytes: 1_000_000, maxUploadFileRequestInBytes: 1_000_000 } }

describe('govdeSiniri', () => {
  it('genel sınırı, multipart için yükleme sınırını, rota kuralını kullanır', () => {
    expect(govdeSiniri('POST', 'application/json', GENEL)).toBe(2_000_000)
    expect(govdeSiniri('PATCH', 'application/json', GENEL)).toBe(2_000_000)
    expect(govdeSiniri('POST', 'multipart/form-data; boundary=x', GENEL)).toBe(5_000_000)
    expect(govdeSiniri('POST', 'application/json', GENEL, MODEL)).toBe(1_000_000)
    expect(govdeSiniri('POST', undefined, undefined)).toBe(2_000_000)
  })

  it('gövdesiz yöntemlerde ve kapatılmış sınırlayıcıda sınır yok', () => {
    expect(govdeSiniri('GET', undefined, GENEL)).toBeNull()
    expect(govdeSiniri('POST', undefined, GENEL, { requestSizeLimiter: false })).toBeNull()
    expect(govdeSiniri('POST', undefined, { ...GENEL, enabled: false })).toBeNull()
  })
})

describe('govdeyiSinirliOku (gerçek HTTP sunucusu)', () => {
  let sunucu: Server
  let port: number
  let isleyiciCalisti = 0

  beforeAll(async () => {
    const app = createApp()
    // Nitro'daki server/middleware/govdeSiniri.ts gibi: rota işleyicisinden önce çalışır
    app.use(defineEventHandler(async (event) => {
      const rota = event.path.startsWith('/api/model/') ? MODEL : undefined
      const sinir = govdeSiniri(event.node.req.method, event.node.req.headers['content-type'], GENEL, rota)
      if (sinir !== null) await govdeyiSinirliOku(event, sinir, KAPANIS_MS)
    }))
    const router = createRouter()
    const json = defineEventHandler(async (event) => {
      isleyiciCalisti++
      const govde = await readBody<{ veri: string }>(event)
      return { uzunluk: govde.veri.length }
    })
    router.post('/api/json', json)
    router.patch('/api/json', json)
    router.post('/api/model/olaylar', json)
    router.post('/api/yukleme', defineEventHandler(async (event) => {
      isleyiciCalisti++
      const dosya = (await readMultipartFormData(event))?.find(p => p.name === 'file')
      return { boyut: dosya?.data.length ?? 0, ad: dosya?.filename }
    }))
    app.use(router)
    sunucu = createServer(toNodeListener(app))
    await new Promise<void>(r => sunucu.listen(0, '127.0.0.1', r))
    port = (sunucu.address() as AddressInfo).port
  })

  afterAll(() => new Promise<void>(r => sunucu.close(() => r())))

  // Gövdeyi Content-Length olmadan (Transfer-Encoding: chunked) parça parça gönderir.
  // `sonsuz` ise ilk parçayı durmadan gönderir: sunucu bağlantıyı kesene kadar (yanıttan sonra da) sürer.
  function gonder(yontem: string, yol: string, parcalar: Buffer[], opts: { icerikTuru?: string, sonsuz?: boolean, basliklar?: Record<string, string> } = {}) {
    return new Promise<{ durum: number, govde: string, kesildi: boolean }>((resolve, reject) => {
      let bitti = false
      let sonuc: { durum: number, govde: string } | undefined
      const istek = request({
        // Her istek kendi bağlantısında: önceki testin bağlantısı yeniden kullanılmasın
        host: '127.0.0.1', port, path: yol, method: yontem, agent: false,
        headers: { 'content-type': opts.icerikTuru ?? 'application/json', ...opts.basliklar }
      }, (yanit) => {
        let govde = ''
        yanit.on('data', (p: Buffer) => govde += p).on('end', () => {
          sonuc = { durum: yanit.statusCode!, govde }
          if (opts.sonsuz) return
          bitti = true
          resolve({ ...sonuc, kesildi: false })
          istek.destroy()
        })
      })
      const kesildi = () => {
        bitti = true
        resolve({ durum: 0, govde: '', ...sonuc, kesildi: true })
      }
      // Sunucu bağlantıyı kesince istemcinin yazmaya çalışması EPIPE/ECONNRESET verebilir
      istek.on('error', e => sonuc || opts.sonsuz ? kesildi() : reject(e)).on('close', kesildi)
      if (opts.basliklar?.['content-length']) {
        istek.end()
        return
      }
      const parca = parcalar[0]!
      let i = 0
      const yaz = () => {
        while (!bitti) {
          if (!opts.sonsuz && i >= parcalar.length) return istek.end()
          const p = opts.sonsuz ? parca : parcalar[i]!
          i++
          if (!istek.write(p)) return istek.once('drain', yaz)
        }
      }
      yaz()
    })
  }

  const jsonParcalari = (uzunluk: number) => {
    const govde = Buffer.from(JSON.stringify({ veri: 'a'.repeat(uzunluk) }))
    const parcalar: Buffer[] = []
    for (let i = 0; i < govde.length; i += 64 * 1024) parcalar.push(govde.subarray(i, i + 64 * 1024))
    return parcalar
  }

  it('sınırın altındaki chunked gövde okunur', async () => {
    const yanit = await gonder('POST', '/api/json', jsonParcalari(500_000))
    expect(yanit.durum).toBe(200)
    expect(JSON.parse(yanit.govde)).toEqual({ uzunluk: 500_000 })
  })

  it('Content-Length olmayan büyük chunked gövde 413 ile reddedilir, işleyiciye ulaşmaz', async () => {
    const once = isleyiciCalisti
    const yanit = await gonder('POST', '/api/json', jsonParcalari(3_000_000))
    expect(yanit.durum).toBe(413)
    expect(isleyiciCalisti).toBe(once)
  })

  it('hiç bitmeyen chunked gövde: işleyiciye ulaşmaz, bekleme süresinden sonra bağlantı kesilir', async () => {
    const once = isleyiciCalisti
    const baslangic = Date.now()
    const yanit = await gonder('POST', '/api/json', [Buffer.alloc(64 * 1024, 'a')], { sonsuz: true })
    // Kesilirken istemci hâlâ yazdığı için 413 yanıtı istemciye ulaşmayabilir (ECONNRESET)
    expect(yanit.kesildi).toBe(true)
    if (yanit.durum) expect(yanit.durum).toBe(413)
    expect(Date.now() - baslangic).toBeGreaterThanOrEqual(KAPANIS_MS - 50)
    expect(Date.now() - baslangic).toBeLessThan(KAPANIS_MS + 2_000)
    expect(isleyiciCalisti).toBe(once)
  })

  it('PATCH de sınırlanır (nuxt-security PATCH\'e bakmaz)', async () => {
    expect((await gonder('PATCH', '/api/json', jsonParcalari(3_000_000))).durum).toBe(413)
    expect((await gonder('PATCH', '/api/json', [], { basliklar: { 'content-length': '3000000' } })).durum).toBe(413)
  })

  it('rota kuralı uygulanır: /api/model/** için 1 MB', async () => {
    expect((await gonder('POST', '/api/model/olaylar', jsonParcalari(1_200_000))).durum).toBe(413)
    expect((await gonder('POST', '/api/model/olaylar', jsonParcalari(900_000))).durum).toBe(200)
  })

  describe('Excel yükleme (multipart)', () => {
    const multipart = (boyut: number) => {
      const sinir = '----chainguardtest'
      const govde = Buffer.concat([
        Buffer.from(`--${sinir}\r\nContent-Disposition: form-data; name="file"; filename="veri.xlsx"\r\n`
          + 'Content-Type: application/octet-stream\r\n\r\n'),
        Buffer.alloc(boyut, 1),
        Buffer.from(`\r\n--${sinir}--\r\n`)
      ])
      const parcalar: Buffer[] = []
      for (let i = 0; i < govde.length; i += 64 * 1024) parcalar.push(govde.subarray(i, i + 64 * 1024))
      return { parcalar, icerikTuru: `multipart/form-data; boundary=${sinir}` }
    }

    it('genel 2 MB sınırının üstündeki dosya, yükleme sınırı altında kaldıkça alınır', async () => {
      const { parcalar, icerikTuru } = multipart(3_000_000)
      const yanit = await gonder('POST', '/api/yukleme', parcalar, { icerikTuru })
      expect(yanit.durum).toBe(200)
      expect(JSON.parse(yanit.govde)).toEqual({ boyut: 3_000_000, ad: 'veri.xlsx' })
    })

    it('yükleme sınırını aşan chunked dosya 413 ile reddedilir', async () => {
      const { parcalar, icerikTuru } = multipart(6_000_000)
      expect((await gonder('POST', '/api/yukleme', parcalar, { icerikTuru })).durum).toBe(413)
    })
  })
})
