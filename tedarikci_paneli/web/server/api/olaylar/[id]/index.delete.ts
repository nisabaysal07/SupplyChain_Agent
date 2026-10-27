// Hatalı veya deneme olaylarını (çıkarımıyla birlikte) yalnızca yönetici kaldırabilir. Model aynı olayı yeniden gönderebilir.
export default defineEventHandler(async (event) => {
  yoneticiGerekli(event)
  const id = getRouterParam(event, 'id') ?? ''
  if (!KIMLIK.test(id) || !await olayGetir(id)) {
    throw createError({ statusCode: 404, statusMessage: 'Olay bulunamadı' })
  }
  await Promise.all([olaySil(id), olayBildirimleriniSil(id)])
  return { tamam: true }
})
