export default defineEventHandler(async (event) => {
  return await bildirimleriGetir(kullaniciGerekli(event).id)
})
