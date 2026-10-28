export default defineEventHandler(async (event) => {
  const kullanici = kullaniciGerekli(event)
  // Yeni sipariş gereken parça varsa bildirimi bu listeye yetişsin
  await stokBildirimleriniKontrolEt()
  return await bildirimleriGetir(kullanici.id)
})
