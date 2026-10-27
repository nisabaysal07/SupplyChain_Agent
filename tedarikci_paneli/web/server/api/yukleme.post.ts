// company_file Excel'ini supply_db'ye aktarır (server/utils/excel.ts + importer.ts). Yalnızca yönetici.
// Mevcut kayıtlar değişmez, yalnızca yenileri eklenir; satır bazında rapor döner.
const EN_BUYUK_BOYUT = 5 * 1024 * 1024 // nuxt-security'nin dosya yükleme sınırıyla aynı

// Türkçe karakterler HTTP durum metninde bozulabilir; mesaj gövdede (data) de gönderilir
const hata = (mesaj: string) => createError({ statusCode: 400, statusMessage: mesaj, data: { message: mesaj } })

export default defineEventHandler(async (event) => {
  yoneticiGerekli(event)

  const parcalar = await readMultipartFormData(event)
  const dosya = parcalar?.find(p => p.name === 'file' && p.filename)
  if (!dosya) throw hata('Dosya seçilmedi.')
  if (!dosya.filename!.toLowerCase().endsWith('.xlsx')) throw hata('Sadece .xlsx dosyası yüklenebilir.')
  if (dosya.data.length > EN_BUYUK_BOYUT) throw hata('Dosya 5 MB sınırını aşıyor.')

  let satirlar
  try {
    satirlar = await parseSupplyExcel(dosya.data)
  }
  catch (e) {
    if (e instanceof ExcelFormatError) throw hata(e.message)
    throw e
  }
  if (!satirlar.length) throw hata('Excel\'de veri satırı yok.')

  let istemci
  try {
    istemci = await yazmaHavuzuGetir().connect()
  }
  catch (e) {
    // Bağlantı ayrıntısı tarayıcıya gönderilmez, yalnızca sunucu günlüğüne yazılır
    console.error('[ChainGuard] Yükleme için veritabanına bağlanılamadı:', (e as Error).message)
    const mesaj = 'Veritabanına ulaşılamadı.'
    throw createError({ statusCode: 503, statusMessage: mesaj, data: { message: mesaj } })
  }
  try {
    return await importRows(istemci, satirlar)
  }
  finally {
    istemci.release()
  }
})
