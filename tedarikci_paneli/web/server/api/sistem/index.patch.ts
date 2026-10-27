export default defineEventHandler(async (event) => {
  yoneticiGerekli(event)
  const ayarlar = await readValidatedBody(event, SistemSemasi.parse)
  await sistemAyarlariKaydet(ayarlar)
  return ayarlar
})
