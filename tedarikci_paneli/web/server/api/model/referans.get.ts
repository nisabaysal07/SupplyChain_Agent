// Model, olayın kapsamını yazarken panelin bildiği adları buradan alır (ülke, liman/havalimanı, HS6, firma, tedarikçi kimlikleri)
export default defineEventHandler(async (event) => {
  modelGerekli(event)
  return await referansVerisi()
})
