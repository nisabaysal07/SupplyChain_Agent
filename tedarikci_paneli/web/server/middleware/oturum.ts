// Bütün /api uçları oturum ister. Açık olanlar: giriş ve modüllerin kendi uçları (/api/_auth, /api/_nuxt_icon).
// /api/model/ uçları kullanıcı oturumu yerine modelin erişim anahtarını ister (server/utils/modelErisimi.ts).
// Kullanıcı her istekte depodan okunur: silinen kullanıcının çerezi geçersiz olur, rol değişikliği hemen yansır.
const ACIK_YOLLAR = ['/api/auth/giris']

export default defineEventHandler(async (event) => {
  const yol = getRequestURL(event).pathname
  if (!yol.startsWith('/api/') || yol.startsWith('/api/_') || yol.startsWith('/api/model/') || ACIK_YOLLAR.includes(yol)) return

  const { user } = await requireUserSession(event, { message: 'Oturum açmanız gerekiyor' })
  const kayit = await kullaniciGetir(user.id)
  if (!kayit) {
    await clearUserSession(event)
    throw createError({ statusCode: 401, statusMessage: 'Oturum geçersiz' })
  }
  event.context.kullanici = kayit
})
