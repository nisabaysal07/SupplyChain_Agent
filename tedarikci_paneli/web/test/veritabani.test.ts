import { copyFileSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { PGlite } from '@electric-sql/pglite'
import { PGLiteSocketServer } from '@electric-sql/pglite-socket'
import pg from 'pg'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { csvleriYukle } from '../db/yukleyici'
import { tedarikcileriBirlestir } from '../server/utils/veri'
import { csvTablolariniOku, postgresTablolariniOku } from '../server/utils/veriKaynagi'
import { havuzOlustur } from '../server/utils/veritabani'

// Gerçek PostgreSQL (PGlite) bir sokette çalışır; uygulamanın kullandığı pg sürücüsüyle bağlanılır
const CSV_KLASORU = resolve(import.meta.dirname, '..', '..')
const PORT = 54_329

let db: PGlite
let sunucu: PGLiteSocketServer
let havuz: pg.Pool

beforeAll(async () => {
  db = await PGlite.create()
  // Uygulamanın havuzu tabloları paralel okur (en fazla 5 bağlantı)
  sunucu = new PGLiteSocketServer({ db, port: PORT, host: '127.0.0.1', maxConnections: 5 })
  await sunucu.start()
  havuz = havuzOlustur(`postgres://postgres@127.0.0.1:${PORT}/postgres?sslmode=disable`)
}, 30_000)

afterAll(async () => {
  await havuz?.end()
  await sunucu?.stop()
  await db?.close()
})

describe('PostgreSQL veri kaynağı', () => {
  it('CSV\'ler şemaya yüklenir', async () => {
    const istemci = await havuz.connect()
    try {
      const sayilar = await csvleriYukle(istemci, CSV_KLASORU)
      expect(sayilar).toEqual({ ulkeler: 4, firmalar: 8, parcalar: 9, tedarikciler: 9, rotalar: 9 })
      // Tekrar yüklemek aynı sonucu verir (tablolar boşaltılıp doldurulur)
      expect(await csvleriYukle(istemci, CSV_KLASORU)).toEqual(sayilar)
    }
    finally {
      istemci.release()
    }
  })

  it('veritabanından okunan tedarikçiler CSV\'den okunanlarla birebir aynı', async () => {
    const pgden = tedarikcileriBirlestir(await postgresTablolariniOku(havuz))
    const csvden = tedarikcileriBirlestir(await csvTablolariniOku(CSV_KLASORU))
    expect(pgden).toHaveLength(9)
    expect(pgden).toEqual(csvden)
  })

  it('tarihler saat dilimi kaymadan "YYYY-AA-GG" olarak gelir', async () => {
    const ted = tedarikcileriBirlestir(await postgresTablolariniOku(havuz))
    expect(ted.find(t => t.firma === 'FSP')!.fiyatTarihi).toBe('2024-04-11')
    expect(ted.every(t => t.sozlesmeBitis === '2026-12-31')).toBe(true)
  })

  it('şema geçersiz değerleri reddeder', async () => {
    await expect(havuz.query('INSERT INTO rotalar VALUES (999, \'roket\', \'a\', \'b\', \'c\', 1)')).rejects.toThrow()
  })

  it('CSV\'lerden biri bozuksa yükleme tamamen geri alınır, eski veri kalır', async () => {
    const klasor = mkdtempSync(join(tmpdir(), 'chainguard-'))
    try {
      for (const ad of ['ulkeler', 'firmalar', 'parcalar', 'tedarikciler', 'rotalar']) {
        copyFileSync(join(CSV_KLASORU, `${ad}.csv`), join(klasor, `${ad}.csv`))
      }
      // Son tablodaki son satır şemaya aykırı: önceki tablolar yazılmış olsa bile hepsi geri alınmalı
      const rotalar = readFileSync(join(klasor, 'rotalar.csv'), 'utf8').replace(/;deniz;Cai Mep Port/, ';roket;Cai Mep Port')
      writeFileSync(join(klasor, 'rotalar.csv'), rotalar)
      await havuz.query('UPDATE firmalar SET firma_adi = \'Eski veri\' WHERE firma_id = 1')

      const istemci = await havuz.connect()
      try {
        await expect(csvleriYukle(istemci, klasor)).rejects.toThrow()
      }
      finally {
        istemci.release()
      }
      const { rows } = await havuz.query('SELECT firma_adi, (SELECT count(*)::int FROM rotalar) AS rota FROM firmalar WHERE firma_id = 1')
      expect(rows[0]).toEqual({ firma_adi: 'Eski veri', rota: 9 })
    }
    finally {
      rmSync(klasor, { recursive: true, force: true })
    }
  })
})
