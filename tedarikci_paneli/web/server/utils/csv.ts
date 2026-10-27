// ";" ayırıcılı, UTF-8 (BOM) CSV okuyucu (build_dataset.py'nin yazdığı biçim). Tırnaklı alanları destekler.
// Başka modül içe aktarmaz: veritabanı yükleme betiği (db/yukle.ts) de doğrudan kullanır.

export type Satir = Record<string, string>

export function csvAyristir(metin: string): Satir[] {
  const satirlar: string[][] = []
  let alan = ''
  let satir: string[] = []
  let tirnakta = false
  const temiz = metin.replace(/^﻿/, '')

  for (let i = 0; i < temiz.length; i++) {
    const c = temiz[i]
    if (tirnakta) {
      if (c === '"' && temiz[i + 1] === '"') { alan += '"'; i++ }
      else if (c === '"') tirnakta = false
      else alan += c
    }
    else if (c === '"') tirnakta = true
    else if (c === ';') { satir.push(alan); alan = '' }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && temiz[i + 1] === '\n') i++
      satir.push(alan); alan = ''
      if (satir.some(v => v !== '')) satirlar.push(satir)
      satir = []
    }
    else alan += c
  }
  if (alan !== '' || satir.length) {
    satir.push(alan)
    satirlar.push(satir)
  }

  const [basliklar, ...veri] = satirlar
  if (!basliklar) return []
  return veri.map(s => Object.fromEntries(basliklar.map((b, i) => [b, s[i] ?? ''])))
}
