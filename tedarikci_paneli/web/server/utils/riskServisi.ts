// Olaylar modelden gelir (server/utils/olayDeposu.ts); risk skoru ve olay etkileri her istekte yeniden hesaplanır

// "Bugün" şirketin saat dilimine göre (Ankara) alınır; sv-SE biçimi YYYY-AA-GG verir
export function bugunISO(): string {
  return new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Istanbul' }).format(new Date())
}

export async function riskliTedarikcileriGetir(bugun = bugunISO()): Promise<RiskliTedarikci[]> {
  const [tedarikciler, olaylar] = await Promise.all([tedarikcileriOku(), olaylariGetir()])
  return tedarikciler.map(t => ({ ...t, risk: riskHesapla(t, olaylar, bugun) }))
}

export async function aktifOlaylariGetir(bugun = bugunISO()): Promise<EtkiliOlay[]> {
  const [tedarikciler, olaylar] = await Promise.all([tedarikcileriOku(), olaylariGetir()])
  return olaylar
    .filter(o => olayAktifMi(o, bugun))
    // Çıkarım listeye konmaz (ayrı uçtan, olay seçilince yüklenir)
    .map(({ cikarim, alinma: _alinma, ...o }) => {
      const etkilenenler = tedarikciler.filter(t => olayEslesir(o, t)).map(t => olayEtkisi(o, t))
      return {
        ...o,
        etkilenenler,
        toplamMaliyetEtkisiUsd: etkilenenler.reduce((top, e) => top + e.maliyetEtkisiUsd, 0),
        analizVar: Boolean(cikarim)
      }
    })
    .sort((a, b) => b.tarih.localeCompare(a.tarih))
}
