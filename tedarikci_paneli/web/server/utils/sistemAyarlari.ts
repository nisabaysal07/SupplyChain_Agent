// Sistem ayarları tüm kullanıcılar için ortaktır ve supply_db.app_settings'te tutulur: tarama (main.py --schedule)
// aynı satırı okur. Tablo eski bir veritabanında yoksa ilk kayıtta oluşturulur (tanımı db/supply_db.sql ile aynı).

const TARAMA_ANAHTARI = 'scan_interval_hours'
// main.py'deki DEFAULT_SCAN_INTERVAL_HOURS ile aynı
const VARSAYILAN_SISTEM: SistemAyarlari = { senkronizasyonSaat: 3 }

const TABLO_SQL = `CREATE TABLE IF NOT EXISTS app_settings (
  key        VARCHAR(50) PRIMARY KEY,
  value      JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)`

export async function sistemAyarlariGetir(): Promise<SistemAyarlari> {
  const havuz = veritabaniHavuzu()
  if (!havuz) return VARSAYILAN_SISTEM
  try {
    const { rows } = await havuz.query<{ value: unknown }>('SELECT value FROM app_settings WHERE key = $1', [TARAMA_ANAHTARI])
    const sonuc = SistemSemasi.safeParse({ senkronizasyonSaat: rows[0]?.value })
    return sonuc.success ? sonuc.data : VARSAYILAN_SISTEM
  }
  catch {
    // Tablo henüz yok: tarama da varsayılanı kullanır
    return VARSAYILAN_SISTEM
  }
}

export async function sistemAyarlariKaydet(ayarlar: SistemAyarlari): Promise<void> {
  const havuz = yazmaHavuzuGetir()
  await havuz.query(TABLO_SQL)
  await havuz.query(
    `INSERT INTO app_settings (key, value) VALUES ($1, $2::jsonb)
     ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()`,
    [TARAMA_ANAHTARI, JSON.stringify(ayarlar.senkronizasyonSaat)])
}

type TaramaSatiri = { started_at: Date, status: TaramaDurumu, triggered_by: string }

export async function sonTaramayiGetir(): Promise<SistemDurumu['sonTarama']> {
  const havuz = veritabaniHavuzu()
  if (!havuz) return null
  try {
    const { rows } = await havuz.query<TaramaSatiri>(
      'SELECT started_at, status, triggered_by FROM scan_logs ORDER BY started_at DESC LIMIT 1')
    const r = rows[0]
    return r ? { baslangic: r.started_at.toISOString(), durum: r.status, otomatik: r.triggered_by === 'schedule' } : null
  }
  catch {
    return null
  }
}
