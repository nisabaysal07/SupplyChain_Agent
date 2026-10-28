import { isIP } from 'node:net'
import type { IncomingHttpHeaders } from 'node:http'

// nuxt-security'nin hız sınırlayıcısı istemci adresini getRequestIP(event, { xForwardedFor: true }) ile alır:
// istemcinin kendi gönderdiği X-Forwarded-For başlığına güvenir, her istekte başka adres yazan sınırı aşar.
// h3'ün getRequestIP'si önce event.context.clientAddress'e baktığı için adres burada belirlenir:
//   - varsayılan: yalnızca TCP bağlantısının adresi (başlıklar yok sayılır)
//   - NUXT_GUVENILIR_IP_BASLIGI tanımlıysa (ör. x-forwarded-for, x-real-ip) o başlık; yalnızca uygulama,
//     bu başlığı kendisi yazan güvenilir bir proxy'nin arkasındaysa tanımlanmalı.
// Başlıkta birden çok adres varsa en sağdaki alınır: onu, uygulamaya en yakın (güvenilir) proxy ekler.
export function istemciAdresi(soketAdresi: string | undefined, basliklar: IncomingHttpHeaders, guvenilirBaslik?: string): string | undefined {
  if (guvenilirBaslik) {
    const deger = basliklar[guvenilirBaslik.trim().toLowerCase()]
    const adres = (Array.isArray(deger) ? deger.join(',') : deger ?? '').split(',').map(a => a.trim()).filter(Boolean).at(-1)
    if (adres && isIP(adres)) return adres
  }
  return soketAdresi
}
