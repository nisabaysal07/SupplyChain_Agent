/**
 * company_file Excel satırlarını supply_db'ye aktarır (db/sql/supply_risk_schema.sql).
 *
 * Kural: Her kayıt önce aranır. Varsa hiçbir şey yapılmaz (güncelleme yok),
 * yoksa eklenir. Aynı dosya kaç kez yüklenirse yüklensin çift kayıt oluşmaz.
 *
 * "Var mı?" kontrolü:
 *   items           -> name
 *   suppliers       -> name
 *   supplier_items  -> supplier_id + item_id + item_model   (tablodaki UNIQUE ile aynı)
 *   contracts       -> supplier_item_id + start_date + end_date
 *   shipments       -> contract_id + transport_mode + exit_location_id + destination_location_id
 *   inventory       -> supplier_item_id                     (tablodaki UNIQUE ile aynı)
 *
 * countries ve locations tablolarına ekleme YAPILMAZ (onlar db/yaml'dan yüklenir); sadece aranır:
 *   ülke     -> countries.iso_code  (ör. 'KOR')
 *   lokasyon -> locations.name      (ör. 'Mersin Limanı')
 * Bulunamazsa o satır hata olarak raporlanır ve hiçbir parçası eklenmez.
 */

export interface Db {
  query(text: string, params?: unknown[]): Promise<{ rows: any[] }>
}

export interface SupplyRow {
  rowNumber: number
  name: string | null
  name_original: string | null
  country: string | null
  item: string | null
  item_model: string | null
  assembly_country: string | null
  contract_start_date: string | null // YYYY-MM-DD
  contract_end_date: string | null
  currency: string | null
  purchase_amount: number | null
  unit_price: number | null
  price_date: string | null // contracts.contract_date kolonuna yazılır
  transport_mode: string | null
  exit_location: string | null
  destination_location: string | null
  shipments_status: string | null
  expected_transit_days: number | null
  item_on_hand: number | null
  item_reserved: number | null
  reorder_point: number | null
  // İsteğe bağlı: sadece veritabanında olmayan YENİ bir ürün eklenirken gerekir
  hs6?: string | null
  gtip?: string | null
  unit?: string | null
  parseError?: string // Excel okunurken hücre hatalıysa doldurulur
}

export const TABLES = ['items', 'suppliers', 'supplier_items', 'contracts', 'shipments', 'inventory'] as const
type Table = (typeof TABLES)[number]
type Counts = Record<Table, number>

export interface ImportReport {
  totalRows: number
  importedRows: number
  inserted: Counts
  alreadyExisted: Counts
  errors: { row: number; message: string }[]
}

const REQUIRED: (keyof SupplyRow)[] = [
  'name', 'country', 'item', 'item_model', 'assembly_country', 'contract_start_date',
  'currency', 'unit_price', 'transport_mode', 'exit_location', 'destination_location',
]
const TRANSPORT_MODES = ['sea', 'air', 'road']
const STATUSES = ['planned', 'in_transit', 'delayed', 'arrived', 'cancelled']

class RowError extends Error {}

const zero = (): Counts => ({ items: 0, suppliers: 0, supplier_items: 0, contracts: 0, shipments: 0, inventory: 0 })

export async function importRows(db: Db, rows: SupplyRow[]): Promise<ImportReport> {
  const report: ImportReport = {
    totalRows: rows.length,
    importedRows: 0,
    inserted: zero(),
    alreadyExisted: zero(),
    errors: [],
  }

  await db.query('BEGIN')
  try {
    // Aynı anda iki yükleme yapılırsa çift kayıt oluşmasın diye sıraya sokar.
    await db.query(`SELECT pg_advisory_xact_lock(hashtext('supply_excel_import'))`)

    for (const row of rows) {
      const ins = zero()
      const ex = zero()
      await db.query('SAVEPOINT row_sp')
      try {
        await importOne(db, row, ins, ex)
        await db.query('RELEASE SAVEPOINT row_sp')
        report.importedRows++
        for (const t of TABLES) {
          report.inserted[t] += ins[t]
          report.alreadyExisted[t] += ex[t]
        }
      } catch (err) {
        // Bu satırın yaptığı her şey geri alınır, diğer satırlar etkilenmez.
        await db.query('ROLLBACK TO SAVEPOINT row_sp')
        const message = err instanceof RowError ? err.message : `Veritabanı hatası: ${(err as Error).message}`
        report.errors.push({ row: row.rowNumber, message })
      }
    }

    await db.query('COMMIT')
  } catch (err) {
    await db.query('ROLLBACK')
    throw err
  }
  return report
}

async function importOne(db: Db, r: SupplyRow, ins: Counts, ex: Counts) {
  // --- 0) Satır kontrolleri (veritabanına dokunmadan) ---
  if (r.parseError) throw new RowError(`Hatalı hücre - ${r.parseError}`)
  const missing = REQUIRED.filter((k) => r[k] === null || r[k] === undefined || r[k] === '')
  if (missing.length) throw new RowError(`Boş zorunlu alan: ${missing.join(', ')}`)

  const mode = r.transport_mode!.toLowerCase()
  if (!TRANSPORT_MODES.includes(mode)) {
    throw new RowError(`transport_mode "${r.transport_mode}" geçersiz (${TRANSPORT_MODES.join(', ')} olmalı)`)
  }
  const status = (r.shipments_status ?? 'planned').toLowerCase()
  if (!STATUSES.includes(status)) {
    throw new RowError(`shipments_status "${r.shipments_status}" geçersiz (${STATUSES.join(', ')} olmalı)`)
  }
  const onHand = r.item_on_hand ?? 0
  const reserved = r.item_reserved ?? 0
  if (reserved > onHand) throw new RowError(`item_reserved (${reserved}) item_on_hand'den (${onHand}) büyük olamaz`)
  if (r.contract_end_date && r.contract_end_date < r.contract_start_date!) {
    throw new RowError('contract_end_date, contract_start_date\'ten önce olamaz')
  }

  // --- 1) Sadece okunan tablolar: önce hepsini bul, eksik varsa hiçbir şey ekleme ---
  const supplierCountryId = await findCountry(db, r.country!, 'country')
  const assemblyCountryId = await findCountry(db, r.assembly_country!, 'assembly_country')
  const exit = await findLocation(db, r.exit_location!)
  const destination = await findLocation(db, r.destination_location!)
  // Menşei = malın çıktığı limanın/havalimanının ülkesi (ör. Intel: montaj VNM, çıkış Penang → MYS)
  const originCountryId = exit.countryId ?? assemblyCountryId

  // --- 2) items ---
  let itemId: number
  const item = await db.query(`SELECT id FROM items WHERE name = $1 LIMIT 1`, [r.item])
  if (item.rows.length) {
    itemId = item.rows[0].id
    ex.items++
  } else {
    const hs6 = digits(r.hs6, 6, 6)
    const gtip = digits(r.gtip, 12, 16)
    if (!hs6 || !gtip) {
      throw new RowError(
        `"${r.item}" ürünü items tablosunda yok. Yeni ürün eklemek için Excel'de hs6 (6 hane) ve gtip (12 hane) kolonlarını doldurun.`)
    }
    const created = await db.query(
      `INSERT INTO items (name, hs6, gtip, unit) VALUES ($1, $2, $3, $4) RETURNING id`,
      [r.item, hs6, gtip, r.unit || 'adet'])
    itemId = created.rows[0].id
    ins.items++
  }

  // --- 3) suppliers ---
  const supplierId = await findOrInsert(db, 'suppliers', ins, ex,
    `SELECT id FROM suppliers WHERE name = $1 LIMIT 1`, [r.name],
    `INSERT INTO suppliers (name, name_original, country_id) VALUES ($1, $2, $3) RETURNING id`,
    [r.name, r.name_original, supplierCountryId])

  // --- 4) supplier_items ---
  const supplierItemId = await findOrInsert(db, 'supplier_items', ins, ex,
    `SELECT id FROM supplier_items WHERE supplier_id = $1 AND item_id = $2 AND item_model = $3 LIMIT 1`,
    [supplierId, itemId, r.item_model],
    `INSERT INTO supplier_items (supplier_id, item_id, item_model, assembly_country_id)
     VALUES ($1, $2, $3, $4) RETURNING id`,
    [supplierId, itemId, r.item_model, assemblyCountryId])

  // --- 5) contracts ---
  const contractId = await findOrInsert(db, 'contracts', ins, ex,
    `SELECT id FROM contracts
      WHERE supplier_item_id = $1 AND start_date = $2::date AND end_date IS NOT DISTINCT FROM $3::date LIMIT 1`,
    [supplierItemId, r.contract_start_date, r.contract_end_date],
    `INSERT INTO contracts (supplier_item_id, start_date, end_date, currency, purchase_amount, unit_price, contract_date)
     VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id`,
    [supplierItemId, r.contract_start_date, r.contract_end_date, r.currency!.toUpperCase(),
     r.purchase_amount, r.unit_price, r.price_date])

  // --- 6) shipments ---
  await findOrInsert(db, 'shipments', ins, ex,
    `SELECT id FROM shipments WHERE contract_id = $1 AND transport_mode = $2
       AND exit_location_id = $3 AND destination_location_id = $4 LIMIT 1`,
    [contractId, mode, exit.id, destination.id],
    `INSERT INTO shipments (contract_id, transport_mode, origin_country_id, exit_location_id,
                            destination_location_id, status, expected_transit_days)
     VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id`,
    [contractId, mode, originCountryId, exit.id, destination.id,
     status, r.expected_transit_days])

  // --- 7) inventory ---
  await findOrInsert(db, 'inventory', ins, ex,
    `SELECT id FROM inventory WHERE supplier_item_id = $1 LIMIT 1`, [supplierItemId],
    `INSERT INTO inventory (supplier_item_id, on_hand, reserved, reorder_point)
     VALUES ($1, $2, $3, $4) RETURNING id`,
    [supplierItemId, onHand, reserved, r.reorder_point])
}

async function findOrInsert(
  db: Db, table: Table, ins: Counts, ex: Counts,
  selectSql: string, selectParams: unknown[],
  insertSql: string, insertParams: unknown[],
): Promise<number> {
  const found = await db.query(selectSql, selectParams)
  if (found.rows.length) {
    ex[table]++
    return found.rows[0].id
  }
  const created = await db.query(insertSql, insertParams)
  ins[table]++
  return created.rows[0].id
}

async function findCountry(db: Db, code: string, column: string): Promise<number> {
  const iso = code.trim().toUpperCase()
  const res = await db.query(`SELECT id FROM countries WHERE iso_code = $1 LIMIT 1`, [iso])
  if (!res.rows.length) {
    throw new RowError(`${column}: "${code}" ülkesi countries tablosunda yok (db/yaml/country.yaml'a ekleyin)`)
  }
  return res.rows[0].id
}

async function findLocation(db: Db, name: string): Promise<{ id: number; countryId: number | null }> {
  const res = await db.query(`SELECT id, country_id FROM locations WHERE name = $1 LIMIT 1`, [name])
  if (!res.rows.length) {
    throw new RowError(`"${name}" lokasyonu locations tablosunda yok (db/yaml/location.yaml'a ekleyin)`)
  }
  return { id: res.rows[0].id, countryId: res.rows[0].country_id ?? null }
}

/** hs6/gtip: sadece rakam; Excel sayıya çevirip baştaki sıfırları sildiyse geri ekler. */
function digits(v: string | null | undefined, minLen: number, maxLen: number): string | null {
  if (v === null || v === undefined) return null
  const s = String(v).trim()
  if (!/^\d+$/.test(s) || s.length > maxLen) return null
  return s.padStart(minLen, '0')
}
