import pg from 'pg'

// PostgreSQL bağlantı havuzu. NUXT_DATABASE_URL boşsa veritabanı kullanılmaz (CSV'den okunur).
// Uygulama yalnızca SELECT yapar; veritabanında salt okunur bir kullanıcı tanımlanması önerilir (db/README.md).

const DATE_OID = 1082

export function havuzOlustur(baglanti: string): pg.Pool {
  return new pg.Pool({
    connectionString: baglanti,
    max: 5,
    connectionTimeoutMillis: 5_000,
    idleTimeoutMillis: 30_000,
    statement_timeout: 5_000,
    application_name: 'chainguard-web',
    // DATE sütunları JavaScript Date'e çevrilmesin: saat dilimi kayması olmadan "YYYY-AA-GG" kalsın
    types: {
      getTypeParser: ((oid: number, bicim?: 'text' | 'binary') =>
        oid === DATE_OID ? (v: string) => v : pg.types.getTypeParser(oid, bicim)) as typeof pg.types.getTypeParser
    }
  })
}

let havuz: pg.Pool | null = null

export function veritabaniHavuzu(): pg.Pool | null {
  const { databaseUrl } = useRuntimeConfig()
  if (!databaseUrl) return null
  havuz ??= havuzOlustur(databaseUrl)
  return havuz
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
