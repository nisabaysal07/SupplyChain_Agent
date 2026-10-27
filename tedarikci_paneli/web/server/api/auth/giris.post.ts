// Kullanıcı yoksa da şifre kontrolü yapılır: yanıt süresinden e-postanın kayıtlı olup olmadığı anlaşılmasın
let sahteOzet: Promise<string> | null = null

export default defineEventHandler(async (event) => {
  const { eposta, sifre } = await readValidatedBody(event, GirisSemasi.parse)
  const kayit = await epostaIleBul(eposta)

  sahteOzet ??= hashPassword('kullanilmayan-sahte-sifre')
  const dogru = await verifyPassword(kayit?.sifreHash ?? await sahteOzet, sifre)
  if (!kayit || !dogru) {
    throw createError({ statusCode: 401, statusMessage: 'E-posta veya şifre hatalı' })
  }

  if (passwordNeedsReHash(kayit.sifreHash)) {
    await kullaniciKaydet({ ...kayit, sifreHash: await hashPassword(sifre) })
  }
  await replaceUserSession(event, { user: oturumBilgisi(kayit), girisZamani: new Date().toISOString() })
  return disaAc(kayit)
})
