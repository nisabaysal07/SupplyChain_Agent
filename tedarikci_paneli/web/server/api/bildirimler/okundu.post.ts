import { z } from 'zod'

// { id } verilirse o bildirim, verilmezse kullanıcının bütün bildirimleri okundu sayılır
const Govde = z.object({ id: z.uuid().optional() })

export default defineEventHandler(async (event) => {
  const { id } = await readValidatedBody(event, Govde.parse)
  await okunduIsaretle(kullaniciGerekli(event).id, id)
  return { tamam: true }
})
