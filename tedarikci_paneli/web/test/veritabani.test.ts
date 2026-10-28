import { readdirSync, readFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { PGlite } from '@electric-sql/pglite'
import { PGLiteSocketServer } from '@electric-sql/pglite-socket'
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest'
import { tedarikcileriOku } from '../server/utils/veri'
import { veritabaniDurumu, veritabaniHavuzu } from '../server/utils/veritabani'

// Gerçek PostgreSQL (PGlite) bir sokette çalışır; uygulama .env'deki POSTGRES_* ile aynı yoldan (pg sürücüsü) bağlanır.
// Şema ve veri, Docker kurulumunun yüklediği dosyalarla aynıdır: db/supply_db.sql, sonra db/data/*.sql
const DB_KLASORU = resolve(import.meta.dirname, '..', '..', '..', 'db')
const PORT = 54_329

// Nuxt otomatik içe aktarımları vitest'te yok; veri.ts bunları çağrı anında global olarak arar
vi.stubGlobal('veritabaniHavuzu', veritabaniHavuzu)
vi.stubGlobal('createError', (h: { statusCode: number, statusMessage: string }) =>
  Object.assign(new Error(h.statusMessage), h))

let db: PGlite
let sunucu: PGLiteSocketServer

beforeAll(async () => {
  db = await PGlite.create()
  await db.exec(readFileSync(join(DB_KLASORU, 'supply_db.sql'), 'utf8'))
  for (const dosya of readdirSync(join(DB_KLASORU, 'data')).filter(d => d.endsWith('.sql')).sort()) {
    await db.exec(readFileSync(join(DB_KLASORU, 'data', dosya), 'utf8'))
  }

  // Uygulamanın havuzu en fazla 5 bağlantı açar
  sunucu = new PGLiteSocketServer({ db, port: PORT, host: '127.0.0.1', maxConnections: 5 })
  await sunucu.start()
  vi.stubEnv('POSTGRES_HOST', '127.0.0.1')
  vi.stubEnv('POSTGRES_PORT', String(PORT))
  vi.stubEnv('POSTGRES_USER', 'postgres')
  vi.stubEnv('POSTGRES_DB', 'postgres')
}, 60_000)

afterAll(async () => {
  await veritabaniHavuzu()?.end()
  await sunucu?.stop()
  await db?.close()
  vi.unstubAllEnvs()
})

describe('PostgreSQL veri kaynağı (supply_db)', () => {
  it('şema ve veri dosyaları yüklenir, uygulama bağlanır', async () => {
    const { rows } = await db.query<{ n: number }>('SELECT count(*)::int AS n FROM supplier_items')
    expect(rows[0]!.n).toBeGreaterThan(0)
    expect(await veritabaniDurumu()).toBe('bagli')
  })

  it('her tedarikçi kaydı eksiksiz okunur', async () => {
    const { rows } = await db.query<{ n: number }>('SELECT count(*)::int AS n FROM supplier_items')
    const ted = await tedarikcileriOku()
    expect(ted).toHaveLength(rows[0]!.n)
    for (const t of ted) {
      expect(t.fiyatUsd).toBeGreaterThan(0)
      expect(['deniz', 'hava']).toContain(t.rota.mod)
      expect(t.stok.kullanilabilir).toBe(t.stok.eldeki - t.stok.rezerve)
      expect(t.yillikAlimUsd).toBe(Math.round(t.fiyatUsd * t.yillikAdet))
    }
  })

  it('tarihler saat dilimi kaymadan "YYYY-AA-GG" olarak gelir', async () => {
    const ted = await tedarikcileriOku()
    const tarih = /^\d{4}-\d{2}-\d{2}$/
    for (const t of ted) {
      expect(t.fiyatTarihi).toMatch(tarih)
      expect(t.sozlesmeBaslangic).toMatch(tarih)
      expect(t.sozlesmeBitis).toMatch(tarih)
    }
    const { rows } = await db.query<{ end_date: string }>(
      'SELECT to_char(end_date, \'YYYY-MM-DD\') AS end_date FROM contracts WHERE supplier_item_id = $1 AND is_active',
      [ted[0]!.id])
    expect(ted[0]!.sozlesmeBitis).toBe(rows[0]!.end_date)
  })

  it('şema geçersiz değerleri reddeder', async () => {
    const havuz = veritabaniHavuzu()!
    await expect(havuz.query('UPDATE shipments SET transport_mode = \'roket\' WHERE id = (SELECT min(id) FROM shipments)'))
      .rejects.toThrow()
    await expect(havuz.query('UPDATE inventory SET reserved = on_hand + 1 WHERE id = (SELECT min(id) FROM inventory)'))
      .rejects.toThrow()
  })

  it('stoğu olmayan kayıt atlanır, diğerleri okunur', async () => {
    const once = await tedarikcileriOku()
    const hedef = once[0]!.id
    const uyari = vi.spyOn(console, 'warn').mockImplementation(() => {})
    await db.query('DELETE FROM inventory WHERE supplier_item_id = $1', [hedef])

    const sonra = await tedarikcileriOku()
    expect(sonra).toHaveLength(once.length - 1)
    expect(sonra.find(t => t.id === hedef)).toBeUndefined()
    expect(uyari).toHaveBeenCalledWith(expect.stringContaining('eksik: stok'))
    uyari.mockRestore()
  })
})
