import ExcelJS from 'exceljs'
import type { SupplyRow } from './importer'

/** Excel başlığı -> SupplyRow alanı. 'contract_date' eski dosyalar için price_date'e eşlenir. */
const HEADER_MAP: Record<string, keyof SupplyRow> = {
  name: 'name',
  name_original: 'name_original',
  country: 'country',
  item: 'item',
  item_model: 'item_model',
  assembly_country: 'assembly_country',
  contract_start_date: 'contract_start_date',
  contract_end_date: 'contract_end_date',
  currency: 'currency',
  purchase_amount: 'purchase_amount',
  unit_price: 'unit_price',
  price_date: 'price_date',
  contract_date: 'price_date',
  transport_mode: 'transport_mode',
  exit_location: 'exit_location',
  destination_location: 'destination_location',
  chokepoint_location: 'chokepoint_location',
  shipments_status: 'shipments_status',
  expected_transit_days: 'expected_transit_days',
  item_on_hand: 'item_on_hand',
  item_reserved: 'item_reserved',
  reorder_point: 'reorder_point',
  // isteğe bağlı kolonlar (sadece yeni ürün eklenirken gerekir)
  hs6: 'hs6',
  gtip: 'gtip',
  unit: 'unit',
}
const OPTIONAL_FIELDS = new Set<keyof SupplyRow>(['hs6', 'gtip', 'unit'])

const NUMBER_FIELDS = new Set<keyof SupplyRow>([
  'purchase_amount', 'unit_price', 'expected_transit_days', 'item_on_hand', 'item_reserved', 'reorder_point',
])
const DATE_FIELDS = new Set<keyof SupplyRow>(['contract_start_date', 'contract_end_date', 'price_date'])

export class ExcelFormatError extends Error {}

export async function parseSupplyExcel(buffer: Buffer): Promise<SupplyRow[]> {
  const wb = new ExcelJS.Workbook()
  try {
    await wb.xlsx.load(buffer as any)
  } catch {
    throw new ExcelFormatError('Dosya okunamadı. Lütfen .xlsx formatında bir Excel yükleyin.')
  }
  const ws = wb.getWorksheet('company_file') ?? wb.worksheets[0]
  if (!ws) throw new ExcelFormatError('Excel dosyasında sayfa bulunamadı.')

  // Başlık satırı: hangi kolonda hangi alan var
  const columns = new Map<number, keyof SupplyRow>()
  ws.getRow(1).eachCell((cell, col) => {
    const header = String(plain(cell.value) ?? '').trim().toLowerCase()
    const field = HEADER_MAP[header]
    if (field) columns.set(col, field)
  })
  const present = new Set(columns.values())
  const missingHeaders = [...new Set(Object.values(HEADER_MAP))].filter((f) => !OPTIONAL_FIELDS.has(f) && !present.has(f))
  if (missingHeaders.length) {
    throw new ExcelFormatError(`Excel'de eksik kolon(lar): ${missingHeaders.join(', ')}`)
  }

  const rows: SupplyRow[] = []
  for (let r = 2; r <= ws.rowCount; r++) {
    const excelRow = ws.getRow(r)
    const row = { rowNumber: r } as SupplyRow
    let hasData = false
    let parseError: string | null = null

    for (const [col, field] of columns) {
      const raw = plain(excelRow.getCell(col).value)
      let value: string | number | null
      try {
        value = DATE_FIELDS.has(field) ? toDate(raw) : NUMBER_FIELDS.has(field) ? toNumber(raw) : toText(raw)
      } catch (e) {
        parseError ??= `${field}: ${(e as Error).message}`
        value = null
      }
      if (value !== null) hasData = true
      ;(row as any)[field] = value
    }

    if (!hasData) continue // tamamen boş satırları atla
    if (parseError) (row as any).parseError = parseError
    rows.push(row)
  }
  return rows
}

/** Formül, zengin metin, link gibi hücre tiplerini düz değere çevirir. */
function plain(v: unknown): unknown {
  if (v === null || v === undefined) return null
  if (v instanceof Date) return v
  if (typeof v === 'object') {
    const o = v as any
    if ('result' in o) return plain(o.result)
    if ('richText' in o) return o.richText.map((t: any) => t.text).join('')
    if ('text' in o) return o.text
    if ('error' in o) return null
  }
  return v
}

function toText(v: unknown): string | null {
  if (v === null) return null
  const s = (v instanceof Date ? v.toISOString().slice(0, 10) : String(v)).trim()
  return s === '' ? null : s
}

function toNumber(v: unknown): number | null {
  if (v === null) return null
  if (typeof v === 'number') return v
  const s = String(v).trim()
  if (s === '') return null
  const n = Number(s.includes(',') && !s.includes('.') ? s.replace(',', '.') : s)
  if (Number.isNaN(n)) throw new Error(`"${s}" sayı değil`)
  return n
}

/** YYYY-MM-DD döner. Excel tarihi, Excel seri numarası, 2026-10-01 veya 01.10.2026 kabul eder. */
function toDate(v: unknown): string | null {
  if (v === null) return null
  if (v instanceof Date) return v.toISOString().slice(0, 10) // exceljs tarihleri UTC verir
  if (typeof v === 'number') {
    return new Date(Date.UTC(1899, 11, 30) + Math.round(v) * 86400000).toISOString().slice(0, 10)
  }
  const s = String(v).trim()
  if (s === '') return null
  let m = s.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (m) return `${m[1]}-${m[2]}-${m[3]}`
  m = s.match(/^(\d{1,2})[./](\d{1,2})[./](\d{4})$/)
  if (m) return `${m[3]}-${m[2].padStart(2, '0')}-${m[1].padStart(2, '0')}`
  throw new Error(`"${s}" tarih değil`)
}
