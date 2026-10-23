import { parseSupplyExcel, ExcelFormatError } from '../utils/excel'
import { importRows } from '../utils/importer'
import { getPool } from '../utils/db'

const MAX_SIZE = 10 * 1024 * 1024 // 10 MB

// Türkçe karakterler HTTP durum metninde bozulur; mesajı gövdede (data) gönderiyoruz.
const fail = (message: string) => createError({ statusCode: 400, message, data: { message } })

export default defineEventHandler(async (event) => {
  const parts = await readMultipartFormData(event)
  const file = parts?.find((p) => p.name === 'file' && p.filename)

  if (!file) throw fail('Dosya seçilmedi.')
  if (!file.filename!.toLowerCase().endsWith('.xlsx')) {
    throw fail('Sadece .xlsx dosyası yüklenebilir.')
  }
  if (file.data.length > MAX_SIZE) {
    throw fail('Dosya 10 MB sınırını aşıyor.')
  }

  let rows
  try {
    rows = await parseSupplyExcel(file.data)
  } catch (e) {
    if (e instanceof ExcelFormatError) throw fail(e.message)
    throw e
  }
  if (!rows.length) throw fail('Excel\'de veri satırı yok.')

  const client = await getPool().connect()
  try {
    return await importRows(client, rows)
  } finally {
    client.release()
  }
})
