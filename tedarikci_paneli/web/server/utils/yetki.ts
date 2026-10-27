import type { H3Event } from 'h3'
import type { KullaniciKaydi } from './kullanicilar'

declare module 'h3' {
  interface H3EventContext {
    kullanici?: KullaniciKaydi
  }
}

// server/middleware/oturum.ts tarafından doldurulur
export function kullaniciGerekli(event: H3Event): KullaniciKaydi {
  const k = event.context.kullanici
  if (!k) throw createError({ statusCode: 401, statusMessage: 'Oturum açmanız gerekiyor' })
  return k
}

export function yoneticiGerekli(event: H3Event): KullaniciKaydi {
  const k = kullaniciGerekli(event)
  if (k.rol !== 'yonetici') throw createError({ statusCode: 403, statusMessage: 'Bu işlem için yönetici yetkisi gerekiyor' })
  return k
}
