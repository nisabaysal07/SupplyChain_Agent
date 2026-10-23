# Tedarik Excel Yükleme (Nuxt)

Şirketlerin `company_file` sayfalı Excel'ini yükleyip `supply_db`'deki `items`, `suppliers`,
`supplier_items`, `contracts`, `shipments` ve `inventory` tablolarına aktardığı tek sayfalık uygulama.

## Çalıştırma

```bash
cd web
npm install
npm run dev        # http://localhost:3000
```

Veritabanı bağlantısı Python betikleriyle aynı: proje kökündeki `.env`
(`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`; isteğe bağlı `POSTGRES_HOST`, `POSTGRES_PORT`,
varsayılan `localhost:5432`). Docker'daki Postgres'in 5432 portu dışarı açık olmalı.

## Kurallar

- Her kayıt önce aranır: **varsa hiçbir şey yapılmaz** (güncellenmez), **yoksa eklenir**.
  Aynı dosyayı tekrar yüklemek güvenlidir.
- `countries` ve `locations` tablolarına ekleme yapılmaz (bunlar `db/yaml` + `download_all.py` ile yönetilir).
  Excel'de olmayan bir ülke kodu ya da lokasyon adı varsa o satır hata olarak raporlanır.
- Hatalı satırın hiçbir parçası yazılmaz; diğer satırlar etkilenmez.

| Tablo | "Var mı?" anahtarı |
|---|---|
| items | name |
| suppliers | name |
| supplier_items | supplier_id + item_id + item_model |
| contracts | supplier_item_id + start_date + end_date |
| shipments | contract_id + transport_mode + exit_location_id + destination_location_id |
| inventory | supplier_item_id |

## Excel → tablo eşlemesi

| Excel | Veritabanı |
|---|---|
| country, assembly_country (ör. `KOR`) | `countries.iso_code` → `suppliers.country_id`, `supplier_items.assembly_country_id` |
| exit_location, destination_location, chokepoint_location | `locations.name` → `shipments.*_location_id` |
| (çıkış lokasyonunun ülkesi) | `shipments.origin_country_id` |
| price_date (ya da contract_date) | `contracts.contract_date` |
| shipments_status (boşsa `planned`) | `shipments.status` |
| item_on_hand / item_reserved / reorder_point | `inventory.on_hand / reserved / reorder_point` |

**Yeni ürün:** `items` tablosunda `hs6`, `gtip`, `unit` zorunlu olduğu için, veritabanında olmayan bir ürünü
eklemek isteyen Excel'e `hs6` ve `gtip` kolonlarını eklemeli (`unit` boşsa `adet`). Bu kolonlar
isteğe bağlıdır; mevcut ürünler için gerekmez.
