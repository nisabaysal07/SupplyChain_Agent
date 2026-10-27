// Modelin bu haber (olay) için yaptığı çıkarım; yoksa null
export default defineEventHandler(async (event): Promise<ModelCikarimi | null> => {
  const id = getRouterParam(event, 'id') ?? ''
  const olay = KIMLIK.test(id) ? await olayGetir(id) : null
  if (!olay) throw createError({ statusCode: 404, statusMessage: 'Olay bulunamadı' })
  return olay.cikarim ?? null
})
