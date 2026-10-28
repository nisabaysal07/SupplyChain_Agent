import type { GuvenlikAyari } from '../utils/govdeSiniri'

// İstek gövdesini akarken sayarak sınırlar (server/utils/govdeSiniri.ts). Gövdeyi okuyan her şeyden
// (nuxt-security'nin XSS süzgeci dahil, o da oturum kontrolünden önce gövde okur) önce çalışmalıdır.
export default defineEventHandler(async (event) => {
  const req = event.node.req
  const sinir = govdeSiniri(req.method, req.headers['content-type'],
    useRuntimeConfig().security as GuvenlikAyari | undefined,
    getRouteRules(event).security as GuvenlikAyari | undefined)
  if (sinir !== null) await govdeyiSinirliOku(event, sinir)
})
