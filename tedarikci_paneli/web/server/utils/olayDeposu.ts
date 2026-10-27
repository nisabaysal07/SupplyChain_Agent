// Modelin gönderdiği olaylar (haber + çıkarım) Nitro deposunda tutulur: .data/veri/olay/<id>
const depo = () => useStorage<KayitliOlay>('veri')
const anahtar = (id: string) => `olay:${id}`

export async function olaylariGetir(): Promise<KayitliOlay[]> {
  const anahtarlar = await depo().getKeys('olay')
  return (await Promise.all(anahtarlar.map(a => depo().getItem(a))))
    .filter((o): o is KayitliOlay => o !== null)
}

export async function olayGetir(id: string): Promise<KayitliOlay | null> {
  return await depo().getItem(anahtar(id))
}

export async function olayKaydet(olay: KayitliOlay): Promise<void> {
  await depo().setItem(anahtar(olay.id), olay)
}

export async function olaySil(id: string): Promise<void> {
  await depo().removeItem(anahtar(id))
}

// Modelin kapsamda kullanabileceği adlar: tedarikçi verisinde geçen ülke, nokta, HS6 ve firma adları
export async function referansVerisi() {
  const t = await tedarikcileriOku()
  const tekil = (degerler: (string | null)[]) => [...new Set(degerler.filter((d): d is string => Boolean(d)))].sort()
  return {
    ulkeler: tekil(t.map(x => x.menseUlke)),
    noktalar: tekil(t.flatMap(x => [x.rota.cikis, x.rota.aktarma, x.rota.varis])),
    hs6: tekil(t.map(x => x.hs6)),
    firmalar: tekil(t.map(x => x.firma)),
    tedarikciler: t.map(x => ({ id: x.id, firma: x.firma, parca: x.parca, menseUlke: x.menseUlke, cikis: x.rota.cikis, varis: x.rota.varis }))
  }
}
