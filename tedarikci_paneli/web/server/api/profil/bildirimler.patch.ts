export default defineEventHandler(async (event) => {
  const kayit = kullaniciGerekli(event)
  const bildirimler = await readValidatedBody(event, BildirimSemasi.parse)
  const guncel = { ...kayit, bildirimler }
  await kullaniciKaydet(guncel)
  return disaAc(guncel)
})
