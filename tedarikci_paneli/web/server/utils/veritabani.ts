import pg from 'pg'

// PostgreSQL (supply_db) bağlantı havuzları. Bağlantı bilgisi proje kökündeki .env'nin POSTGRES_* değerlerinden
// alınır (Docker'daki proje_postgres konteyneri; db/*.py betikleriyle aynı kullanıcı).
// POSTGRES_USER / POSTGRES_DB boşsa veritabanı kullanılmaz.

const DATE_OID = 1082

function postgresAyarlari(): pg.PoolConfig | null {
  const { POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB } = process.env
  if (!POSTGRES_USER || !POSTGRES_DB) return null
  return {
    host: POSTGRES_HOST || 'localhost',
    port: Number(POSTGRES_PORT || 5432),
    user: POSTGRES_USER,
    password: POSTGRES_PASSWORD,
    database: POSTGRES_DB,
    connectionTimeoutMillis: 5_000,
    // DATE sütunları JavaScript Date'e çevrilmesin: saat dilimi kayması olmadan "YYYY-AA-GG" kalsın
    types: {
      getTypeParser: ((oid: number, bicim?: 'text' | 'binary') =>
        oid === DATE_OID ? (v: string) => v : pg.types.getTypeParser(oid, bicim)) as typeof pg.types.getTypeParser
    }
  }
}

export function veritabaniTanimli(): boolean {
  return postgresAyarlari() !== null
}

// Okuma havuzu: arayüzün sorguları kısa sürmeli
let havuz: pg.Pool | null = null

export function veritabaniHavuzu(): pg.Pool | null {
  if (havuz) return havuz
  const ayarlar = postgresAyarlari()
  if (!ayarlar) return null
  havuz = new pg.Pool({
    ...ayarlar,
    max: 5,
    idleTimeoutMillis: 30_000,
    statement_timeout: 5_000,
    application_name: 'chainguard-web'
  })
  return havuz
}

// Excel yükleme supply_db'ye yazar; içe aktarma uzun sürebileceği için sorgu süre sınırı yoktur.
let yazmaHavuzu: pg.Pool | null = null

export function yazmaHavuzuGetir(): pg.Pool {
  if (yazmaHavuzu) return yazmaHavuzu
  const ayarlar = postgresAyarlari()
  if (!ayarlar) {
    throw createError({ statusCode: 503, statusMessage: 'POSTGRES_USER / POSTGRES_DB tanımlı değil (proje kökündeki .env)' })
  }
  yazmaHavuzu = new pg.Pool({ ...ayarlar, max: 2, application_name: 'chainguard-yukleme' })
  return yazmaHavuzu
}

export async function veritabaniDurumu(): Promise<'bagli' | 'hata' | 'kapali'> {
  const h = veritabaniHavuzu()
  if (!h) return 'kapali'
  try {
    await h.query('SELECT 1')
    return 'bagli'
  }
  catch (e) {
    console.error('[ChainGuard] Veritabanı bağlantı hatası:', (e as Error).message)
    return 'hata'
  }
}
