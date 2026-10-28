import { createError, setResponseHeader, type H3Event } from 'h3'

// nuxt-security'nin requestSizeLimiter'ı yalnızca Content-Length başlığına bakar (yalnızca POST/PUT/DELETE):
// başlıksız (chunked) gövdeler ve PATCH istekleri sınırsız belleğe okunur. Burada gövde akarken sayılır;
// sınıra ulaşınca biriktirme durur ve 413 döner. Sınırlar nuxt-security ayarlarından gelir
// (nuxt.config.ts → security.requestSizeLimiter ve routeRules), bu yüzden ayarlar tek yerde kalır.

const GOVDELI_YONTEMLER = ['POST', 'PUT', 'PATCH', 'DELETE']
// h3'ün readRawBody'si gövdeyi önce burada arar; okunan gövde sonraki readBody/readMultipartFormData çağrılarına buradan verilir
const HAM_GOVDE = Symbol.for('h3RawBody')

// nuxt-security varsayılanları (node_modules/nuxt-security/dist/defaultConfig.mjs)
const VARSAYILAN = { maxRequestSizeInBytes: 2_000_000, maxUploadFileRequestInBytes: 8_000_000 }

type BoyutAyari = false | { maxRequestSizeInBytes?: number, maxUploadFileRequestInBytes?: number }
export interface GuvenlikAyari { enabled?: boolean, requestSizeLimiter?: BoyutAyari }

// Bu istek için gövde sınırı (bayt); sınır yoksa null. Rota kuralı genel ayarın üstüne yazılır.
export function govdeSiniri(yontem: string | undefined, icerikTuru: string | undefined,
  genel?: GuvenlikAyari, rota?: GuvenlikAyari): number | null {
  if (!yontem || !GOVDELI_YONTEMLER.includes(yontem)) return null
  if ((rota?.enabled ?? genel?.enabled) === false) return null
  const ayar = rota?.requestSizeLimiter ?? genel?.requestSizeLimiter
  if (ayar === false) return null
  const sinirlar = { ...VARSAYILAN, ...(genel?.requestSizeLimiter || {}), ...(rota?.requestSizeLimiter || {}) }
  return icerikTuru?.includes('multipart/form-data') ? sinirlar.maxUploadFileRequestInBytes : sinirlar.maxRequestSizeInBytes
}

// Sınır aşıldı: kalan gövde belleğe alınmadan atılır. Yanıt, istemci göndermeyi bitirince verilir; gönderirken
// bağlantı kesilirse istemci 413 yerine bağlantı hatası görür. Gövde `kapanisMs` içinde bitmezse beklenmez,
// yanıttan sonra bağlantı kapatılır (kalan gövde hiç okunmaz).
async function cokBuyuk(event: H3Event, kapanisMs: number) {
  const { req } = event.node
  req.resume()
  const bitti = req.complete || await new Promise<boolean>((resolve) => {
    const zamanlayici = setTimeout(() => resolve(false), kapanisMs)
    req.once('end', () => {
      clearTimeout(zamanlayici)
      resolve(true)
    }).once('close', () => {
      clearTimeout(zamanlayici)
      resolve(req.complete)
    })
  })
  if (!bitti) setResponseHeader(event, 'connection', 'close')
  return createError({ statusCode: 413, statusMessage: 'Payload Too Large' })
}

// Gövdeyi en fazla `sinir` bayta kadar okur (nuxt-security gibi sinir ve üstü reddedilir)
export async function govdeyiSinirliOku(event: H3Event, sinir: number, kapanisMs = 5_000): Promise<void> {
  const req = event.node.req as typeof event.node.req & Record<symbol, unknown> & { rawBody?: unknown, body?: unknown }
  // Gövde zaten bellekte (ör. Nitro'nun sunucu içi $fetch'i): okunacak akış yok
  if (event._requestBody || event.web?.request?.body || req[HAM_GOVDE] || req.rawBody || req.body) return

  const bildirilen = Number.parseInt(req.headers['content-length'] ?? '')
  if (bildirilen >= sinir) throw await cokBuyuk(event, kapanisMs)
  // h3 de bu durumda gövde okumaz
  if (!bildirilen && !/\bchunked\b/i.test(String(req.headers['transfer-encoding'] ?? ''))) return

  // Sınır aşılırsa null
  const govde = await new Promise<Buffer | null>((resolve, reject) => {
    const parcalar: Buffer[] = []
    let boyut = 0
    const birak = () => {
      req.off('data', veri).off('end', bitti).off('error', hata)
    }
    const veri = (parca: Buffer) => {
      boyut += parca.length
      if (boyut >= sinir) {
        birak()
        resolve(null)
        return
      }
      parcalar.push(parca)
    }
    const bitti = () => {
      birak()
      resolve(Buffer.concat(parcalar))
    }
    const hata = (e: Error) => {
      birak()
      reject(e)
    }
    req.on('data', veri).on('end', bitti).on('error', hata)
  })
  if (!govde) throw await cokBuyuk(event, kapanisMs)
  req[HAM_GOVDE] = Promise.resolve(govde)
}
