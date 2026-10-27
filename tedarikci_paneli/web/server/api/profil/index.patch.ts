export default defineEventHandler(async (event) => {
  const kayit = kullaniciGerekli(event)
  const { ad, soyad } = await readValidatedBody(event, ProfilSemasi.parse)
  const guncel = { ...kayit, ad, soyad }
  await kullaniciKaydet(guncel)
  // Oturumdaki ad da güncellenir (menüde görünen ad)
  await setUserSession(event, { user: oturumBilgisi(guncel) })
  return disaAc(guncel)
})
