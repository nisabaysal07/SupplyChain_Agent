import { createHash, timingSafeEqual } from 'node:crypto'
import type { H3Event } from 'h3'

// Model, kullanıcı oturumu yerine gizli bir erişim anahtarıyla (NUXT_MODEL_API_TOKEN) gelir:
//   Authorization: Bearer <anahtar>

const EN_KISA_ANAHTAR = 32

// Sabit sürede karşılaştırma: yanıt süresinden anahtar tahmin edilemez
export function anahtarDogruMu(gelen: string | undefined, beklenen: string): boolean {
  if (!gelen || !beklenen) return false
  const a = createHash('sha256').update(gelen).digest()
  const b = createHash('sha256').update(beklenen).digest()
  return timingSafeEqual(a, b)
}

export function modelGerekli(event: H3Event): void {
  const { modelApiToken } = useRuntimeConfig()
  if (!modelApiToken || modelApiToken.length < EN_KISA_ANAHTAR) {
    throw createError({ statusCode: 503, statusMessage: 'Model erişimi yapılandırılmamış' })
  }
  const baslik = getHeader(event, 'authorization')
  const gelen = baslik?.startsWith('Bearer ') ? baslik.slice(7).trim() : undefined
  if (!anahtarDogruMu(gelen, modelApiToken)) {
    throw createError({ statusCode: 401, statusMessage: 'Geçersiz erişim anahtarı' })
  }
}
