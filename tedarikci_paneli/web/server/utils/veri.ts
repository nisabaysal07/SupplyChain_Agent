// Tedarikçi verisi supply_db'den (.env'deki POSTGRES_* ile Docker'daki Postgres) okunur.
// Her supplier_items satırı bir tedarikçi kaydıdır: fiyat ve tarihler aktif sözleşmeden, rota en son sevkiyattan,
// stok inventory'den, vergi ise parçanın birleştirme (menşe) ülkesine göre geçerli tarifeden gelir.
// Yıllık alım adedi supplier_items.annual_quantity'dir (maliyet_etkisi/maliyet_formulu.py ile aynı kaynak).

const TASIMA_MODLARI: Record<string, TasimaModu> = { sea: 'deniz', air: 'hava' }

const TEDARIKCI_SORGUSU = `
  SELECT si.id, si.annual_quantity,
         i.name AS parca, i.hs6, i.gtip,
         s.name AS firma, s.name_original AS firma_resmi_ad,
         mc.name_tr AS mense_ulke, mc.has_trade_agreement AS anlasma_var,
         t.gv_rate, t.igv_rate,
         c.unit_price, c.currency, c.contract_date, c.start_date, c.end_date,
         sh.transport_mode, cikis.name AS cikis, varis.name AS varis, sh.expected_transit_days,
         inv.on_hand, inv.reserved, inv.reorder_point
  FROM supplier_items si
  JOIN suppliers s ON s.id = si.supplier_id
  JOIN items i ON i.id = si.item_id
  LEFT JOIN countries mc ON mc.id = si.assembly_country_id
  LEFT JOIN LATERAL (
    SELECT * FROM contracts c
    WHERE c.supplier_item_id = si.id AND c.is_active
    ORDER BY c.start_date DESC NULLS LAST, c.id DESC LIMIT 1
  ) c ON true
  LEFT JOIN LATERAL (
    SELECT * FROM shipments sh WHERE sh.contract_id = c.id ORDER BY sh.id DESC LIMIT 1
  ) sh ON true
  LEFT JOIN locations cikis ON cikis.id = sh.exit_location_id
  LEFT JOIN locations varis ON varis.id = sh.destination_location_id
  LEFT JOIN LATERAL (
    SELECT * FROM tariffs t
    WHERE t.item_id = i.id AND t.country_id = si.assembly_country_id
      AND t.valid_from <= CURRENT_DATE AND (t.valid_to IS NULL OR t.valid_to >= CURRENT_DATE)
    ORDER BY t.valid_from DESC LIMIT 1
  ) t ON true
  LEFT JOIN inventory inv ON inv.supplier_item_id = si.id
  WHERE s.is_active
  ORDER BY si.id`

type TedarikciSatiri = {
  id: number
  annual_quantity: number | null
  parca: string
  hs6: string
  gtip: string
  firma: string
  firma_resmi_ad: string | null
  mense_ulke: string | null
  anlasma_var: boolean | null
  gv_rate: string | null
  igv_rate: string | null
  unit_price: string | null
  currency: string | null
  contract_date: string | null
  start_date: string | null
  end_date: string | null
  transport_mode: string | null
  cikis: string | null
  varis: string | null
  expected_transit_days: number | null
  on_hand: string | null
  reserved: string | null
  reorder_point: string | null
}

// Arayüz her alanı dolu bekler; sözleşmesi, sevkiyatı, stoğu veya tarifesi eksik kayıt atlanır
function eksikAlanlar(r: TedarikciSatiri): string[] {
  const eksik: string[] = []
  if (!r.mense_ulke) eksik.push('birleştirme ülkesi')
  if (r.unit_price === null || !r.start_date || !r.end_date) eksik.push('aktif sözleşme')
  if (r.currency && r.currency.trim() !== 'USD') eksik.push(`USD sözleşme (${r.currency.trim()})`)
  if (!r.transport_mode || !TASIMA_MODLARI[r.transport_mode] || !r.cikis || !r.varis) eksik.push('sevkiyat')
  if (r.on_hand === null) eksik.push('stok')
  if (r.gv_rate === null) eksik.push('tarife')
  if (r.annual_quantity === null) eksik.push('yıllık adet')
  return eksik
}

function tedarikciyeCevir(r: TedarikciSatiri): Tedarikci {
  const eldeki = Number(r.on_hand)
  const rezerve = Number(r.reserved ?? 0)
  const siparisSeviyesi = Number(r.reorder_point ?? 0)
  const kullanilabilir = eldeki - rezerve
  const fiyatUsd = Number(r.unit_price)
  const yillikAdet = Number(r.annual_quantity)

  return {
    id: r.id,
    parca: r.parca,
    hs6: r.hs6,
    gtip12: r.gtip,
    firma: r.firma,
    firmaResmiAd: r.firma_resmi_ad ?? r.firma,
    menseUlke: r.mense_ulke!,
    anlasmaVar: Boolean(r.anlasma_var),
    // tariffs tablosundaki oranlar menşe ülkeye göre zaten uygulanmış hâlidir
    vergi: {
      gumrukVergisi: Number(r.gv_rate),
      ilaveGumrukVergisi: Number(r.igv_rate ?? 0)
    },
    birlestirmeUlke: r.mense_ulke!,
    fiyatUsd,
    fiyatTarihi: r.contract_date ?? r.start_date!,
    sozlesmeBaslangic: r.start_date!,
    sozlesmeBitis: r.end_date!,
    rota: {
      mod: TASIMA_MODLARI[r.transport_mode!]!,
      cikis: r.cikis!,
      aktarma: null,
      varis: r.varis!,
      transitGun: Number(r.expected_transit_days ?? 0)
    },
    stok: {
      eldeki,
      rezerve,
      kullanilabilir,
      siparisSeviyesi,
      durum: kullanilabilir < siparisSeviyesi ? 'siparis_gerekli' : 'yeterli'
    },
    yillikAdet,
    yillikAlimUsd: Math.round(fiyatUsd * yillikAdet)
  }
}

export async function tedarikcileriOku(): Promise<Tedarikci[]> {
  const havuz = veritabaniHavuzu()
  if (!havuz) {
    throw createError({ statusCode: 503, statusMessage: 'Veritabanı tanımlı değil (proje kökündeki .env: POSTGRES_*)' })
  }

  let satirlar: TedarikciSatiri[]
  try {
    satirlar = (await havuz.query<TedarikciSatiri>(TEDARIKCI_SORGUSU)).rows
  }
  catch (e) {
    console.error('[ChainGuard] Tedarikçi sorgusu başarısız:', (e as Error).message)
    throw createError({ statusCode: 503, statusMessage: 'Veritabanından tedarikçi verisi okunamadı' })
  }

  const tedarikciler: Tedarikci[] = []
  for (const r of satirlar) {
    const eksik = eksikAlanlar(r)
    if (eksik.length) {
      console.warn(`[ChainGuard] Tedarikçi ${r.id} (${r.firma} – ${r.parca}) atlandı, eksik: ${eksik.join(', ')}`)
      continue
    }
    tedarikciler.push(tedarikciyeCevir(r))
  }
  return tedarikciler
}

type KonumSatiri = { name: string, latitude: string, longitude: string, city: string | null }

// Harita konumları ayrı okunur: sütunları olmayan eski bir veritabanında tedarikçi listesi yine çalışsın
// (sütunları eklemek ve doldurmak için: python db/location_download.py)
export async function konumlariOku(): Promise<Record<string, HaritaKonumu>> {
  const havuz = veritabaniHavuzu()
  if (!havuz) return {}
  try {
    const { rows } = await havuz.query<KonumSatiri>(
      'SELECT name, latitude, longitude, city FROM locations WHERE latitude IS NOT NULL AND longitude IS NOT NULL')
    return Object.fromEntries(rows.map(r => [r.name, { enlem: Number(r.latitude), boylam: Number(r.longitude), bolge: r.city ?? r.name }]))
  }
  catch (e) {
    console.error('[ChainGuard] Harita konumları okunamadı (python db/location_download.py çalıştırıldı mı?):', (e as Error).message)
    return {}
  }
}
