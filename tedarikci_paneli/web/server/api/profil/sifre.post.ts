export default defineEventHandler(async (event) => {
  const kayit = kullaniciGerekli(event)
  const { mevcut, yeni } = await readValidatedBody(event, SifreSemasi.parse)

  if (!await verifyPassword(kayit.sifreHash, mevcut)) {
    throw createError({ statusCode: 400, statusMessage: 'Mevcut şifre hatalı' })
  }
  await kullaniciKaydet({ ...kayit, sifreHash: await hashPassword(yeni) })
  // Şifre değişince oturum yenilenir
  await replaceUserSession(event, { user: oturumBilgisi(kayit), girisZamani: new Date().toISOString() })
  return { tamam: true }
})
