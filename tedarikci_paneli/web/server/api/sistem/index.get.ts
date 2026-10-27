export default defineEventHandler(async (): Promise<SistemDurumu> => {
  const { tavilyApiKey, nemotronApiKey } = useRuntimeConfig()
  return {
    ...await sistemAyarlariGetir(),
    anahtarlar: { tavily: Boolean(tavilyApiKey), nemotron: Boolean(nemotronApiKey) },
    veriKaynagi: { tur: veritabaniTanimli() ? 'postgresql' : 'yok', durum: await veritabaniDurumu() }
  }
})
