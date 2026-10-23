import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import pg from 'pg'

// DATE kolonlarını JS Date'e çevirme, '2026-10-01' olarak bırak (saat dilimi kayması olmasın)
pg.types.setTypeParser(1082, (v) => v)

/**
 * Python betikleriyle (db/yaml_db.py) aynı bağlantı ayarlarını kullanır:
 * proje kökündeki .env -> POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB,
 * isteğe bağlı POSTGRES_HOST (varsayılan localhost), POSTGRES_PORT (varsayılan 5432).
 * Ortamda zaten tanımlı değerler ezilmez.
 */
function loadEnv() {
  for (const path of [resolve(process.cwd(), '../.env'), resolve(process.cwd(), '.env')]) {
    if (!existsSync(path)) continue
    for (let line of readFileSync(path, 'utf8').split(/\r?\n/)) {
      line = line.trim()
      if (!line || line.startsWith('#') || !line.includes('=')) continue
      const i = line.indexOf('=')
      const key = line.slice(0, i).trim()
      const value = line.slice(i + 1).trim().replace(/^["']|["']$/g, '')
      if (process.env[key] === undefined) process.env[key] = value
    }
  }
}

let pool: pg.Pool | null = null

export function getPool(): pg.Pool {
  if (!pool) {
    loadEnv()
    const { POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB } = process.env
    if (!POSTGRES_USER || !POSTGRES_DB) {
      throw new Error('POSTGRES_USER / POSTGRES_DB bulunamadı (proje kökündeki .env dosyasını kontrol edin).')
    }
    pool = new pg.Pool({
      host: process.env.POSTGRES_HOST || 'localhost',
      port: Number(process.env.POSTGRES_PORT || 5432),
      user: POSTGRES_USER,
      password: POSTGRES_PASSWORD,
      database: POSTGRES_DB,
    })
  }
  return pool
}
