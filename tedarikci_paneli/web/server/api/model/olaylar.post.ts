// Modelin bir haberi (olayı) ve isteğe bağlı olarak o haberden yaptığı çıkarımı gönderdiği uç.
// Aynı id ile tekrar gönderilen olay öncekinin yerine geçer (ör. çıkarım sonradan eklendiğinde).
export default defineEventHandler(async (event) => {
  modelGerekli(event)

  const sonuc = ModelOlaySemasi.safeParse(await readBody(event))
  if (!sonuc.success) {
    // Modelin geliştiricisi hatayı düzeltebilsin diye hangi alanın neden reddedildiği döner
    throw createError({
      statusCode: 400,
      statusMessage: 'Olay biçimi geçersiz',
      data: sonuc.error.issues.slice(0, 20).map(i => ({ alan: i.path.join('.'), hata: i.message }))
    })
  }

  const onceki = await olayGetir(sonuc.data.id)
  const olay = { ...sonuc.data, alinma: new Date().toISOString() }
  await olayKaydet(olay)
  // Yeni haber veya yeni çıkarım: tercihleri uyan kullanıcılara uygulama içi bildirim
  const bildirilen = await olayBildirimiGonder(onceki, olay)
  setResponseStatus(event, onceki ? 200 : 201)
  return {
    id: sonuc.data.id,
    durum: onceki ? 'guncellendi' : 'olusturuldu',
    bildirilenKullanici: bildirilen,
    // Eşleşmeyen adlar yazım hatası olabilir: olay kaydedilir ama o ölçüt hiçbir tedarikçiyi etkilemez
    uyarilar: kapsamUyarilari(sonuc.data.kapsam, await referansVerisi())
  }
})
