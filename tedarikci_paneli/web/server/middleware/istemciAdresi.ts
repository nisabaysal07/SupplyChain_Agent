// İstemci adresini hız sınırlayıcıdan (nuxt-security) önce belirler; açıklaması server/utils/istemciAdresi.ts
export default defineEventHandler((event) => {
  const { socket, headers } = event.node.req
  const adres = istemciAdresi(socket.remoteAddress, headers, useRuntimeConfig().guvenilirIpBasligi)
  if (adres) event.context.clientAddress = adres
})
