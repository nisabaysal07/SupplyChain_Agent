import { readFile } from 'node:fs/promises'
import { join } from 'node:path'
import type { ClientBase } from 'pg'
import { csvAyristir } from '../server/utils/csv.ts'
import { SUTUNLAR, TABLO_SIRASI } from '../server/utils/veriKaynagi.ts'

// CSV'leri PostgreSQL'e yükler: şemayı kurar, tabloları boşaltıp yeniden doldurur.
// Hepsi tek işlemdedir (transaction): bir satır bile hatalıysa veritabanı eski hâlinde kalır.

export async function semayiKur(istemci: ClientBase): Promise<void> {
  await istemci.query(await readFile(new URL('./sema.sql', import.meta.url), 'utf8'))
}

export async function csvleriYukle(istemci: ClientBase, klasor: string): Promise<Record<string, number>> {
  const sayilar: Record<string, number> = {}
  await istemci.query('BEGIN')
  try {
    await semayiKur(istemci)
    await istemci.query(`TRUNCATE ${[...TABLO_SIRASI].reverse().join(', ')}`)
    for (const ad of TABLO_SIRASI) {
      const satirlar = csvAyristir(await readFile(join(klasor, `${ad}.csv`), 'utf8'))
      const sutunlar = SUTUNLAR[ad]
      // CSV başlıkları beklenen sütunlarla birebir aynı olmalı (adlar SQL'e yalnızca sabit listeden girer)
      const basliklar = Object.keys(satirlar[0] ?? {})
      if (satirlar.length && basliklar.join() !== sutunlar.join()) {
        throw new Error(`${ad}.csv sütunları beklenenden farklı: ${basliklar.join(', ')}`)
      }
      const yer = sutunlar.map((_, i) => `$${i + 1}`).join(', ')
      for (const s of satirlar) {
        await istemci.query(`INSERT INTO ${ad} (${sutunlar.join(', ')}) VALUES (${yer})`, sutunlar.map(c => s[c]))
      }
      sayilar[ad] = satirlar.length
    }
    await istemci.query('COMMIT')
    return sayilar
  }
  catch (e) {
    await istemci.query('ROLLBACK')
    throw e
  }
}
