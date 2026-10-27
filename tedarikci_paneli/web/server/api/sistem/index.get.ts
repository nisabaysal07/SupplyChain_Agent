export default defineEventHandler(async (): Promise<SistemDurumu> => {
  const { tavilyApiKey, nemotronApiKey, databaseUrl } = useRuntimeConfig()
  return {
    ...await sistemAyarlariGetir(),
    anahtarlar: { tavily: Boolean(tavilyApiKey), nemotron: Boolean(nemotronApiKey) },
    veriKaynagi: { tur: databaseUrl ? 'postgresql' : 'csv', durum: await veritabaniDurumu() }
  }
})
