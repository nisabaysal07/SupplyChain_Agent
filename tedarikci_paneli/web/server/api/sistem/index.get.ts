export default defineEventHandler(async (): Promise<SistemDurumu> => {
  const { modelApiToken } = useRuntimeConfig()
  // Tarama (main.py, agent_core, notify.py) aynı .env'i kullanır; panel onu --dotenv ile yükler
  const tanimli = (degisken: string) => Boolean(process.env[degisken]?.trim())
  const [ayarlar, sonTarama, durum] = await Promise.all([sistemAyarlariGetir(), sonTaramayiGetir(), veritabaniDurumu()])
  return {
    ...ayarlar,
    anahtarlar: {
      tavily: tanimli('TAVILY_API_KEY'),
      nebius: tanimli('NEBIUS_API_KEY'),
      modelErisimi: Boolean(modelApiToken),
      bildirimKanallari: tanimli('NOTIFY_URLS')
    },
    sonTarama,
    veriKaynagi: { tur: veritabaniTanimli() ? 'postgresql' : 'yok', durum }
  }
})
