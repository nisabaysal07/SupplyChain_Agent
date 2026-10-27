-- ChainGuard tedarikçi veri şeması (PostgreSQL)
-- Tablo ve sütun adları build_dataset.py'nin ürettiği CSV'lerle birebir aynıdır (VERI_SOZLUGU.md).
-- Tekrar çalıştırılabilir: tablolar yoksa oluşturulur, varsa dokunulmaz.

CREATE TABLE IF NOT EXISTS ulkeler (
  ulke_id         integer PRIMARY KEY,
  ulke_adi        text    NOT NULL UNIQUE,
  anlasma_durumu  smallint NOT NULL CHECK (anlasma_durumu IN (0, 1)),
  gv_carpani      numeric(4, 2) NOT NULL CHECK (gv_carpani >= 0),
  igv_carpani     numeric(4, 2) NOT NULL CHECK (igv_carpani >= 0)
);

CREATE TABLE IF NOT EXISTS firmalar (
  firma_id     integer PRIMARY KEY,
  firma_adi    text NOT NULL,
  resmi_ad     text NOT NULL,
  merkez_ulke  text NOT NULL
);

CREATE TABLE IF NOT EXISTS parcalar (
  parca_id                  integer PRIMARY KEY,
  parca_adi                 text NOT NULL UNIQUE,
  hs6                       char(6)  NOT NULL CHECK (hs6 ~ '^[0-9]{6}$'),
  gtip12                    char(12) NOT NULL CHECK (gtip12 ~ '^[0-9]{12}$'),
  tarife_gv_tercihsiz       numeric(6, 4) NOT NULL CHECK (tarife_gv_tercihsiz >= 0),
  tarife_igv_tercihsiz      numeric(6, 4) NOT NULL CHECK (tarife_igv_tercihsiz >= 0),
  kultur_fonu_orani         numeric(6, 4) NOT NULL CHECK (kultur_fonu_orani >= 0),
  otv_orani                 numeric(6, 4) NOT NULL CHECK (otv_orani >= 0),
  kdv_orani                 numeric(6, 4) NOT NULL CHECK (kdv_orani >= 0),
  oran_kaynagi              text NOT NULL,
  eldeki_stok               integer NOT NULL CHECK (eldeki_stok >= 0),
  rezerve_stok              integer NOT NULL CHECK (rezerve_stok >= 0),
  yeniden_siparis_seviyesi  integer NOT NULL CHECK (yeniden_siparis_seviyesi > 0)
);

CREATE TABLE IF NOT EXISTS tedarikciler (
  tedarikci_id        integer PRIMARY KEY,
  parca_id            integer NOT NULL REFERENCES parcalar (parca_id),
  firma_id            integer NOT NULL REFERENCES firmalar (firma_id),
  mense_ulke_id       integer NOT NULL REFERENCES ulkeler (ulke_id),
  birlestirme_ulke    text    NOT NULL,
  perakende_usd       numeric(12, 2) NOT NULL CHECK (perakende_usd >= 0),
  fiyat_tarihi        date NOT NULL,
  sozlesme_baslangic  date NOT NULL,
  sozlesme_bitis      date NOT NULL,
  CHECK (sozlesme_bitis >= sozlesme_baslangic)
);

CREATE TABLE IF NOT EXISTS rotalar (
  tedarikci_id     integer PRIMARY KEY REFERENCES tedarikciler (tedarikci_id),
  tasima_modu      text NOT NULL CHECK (tasima_modu IN ('deniz', 'hava')),
  cikis_noktasi    text NOT NULL,
  aktarma_noktasi  text NOT NULL,
  varis_noktasi    text NOT NULL,
  transit_gun      integer NOT NULL CHECK (transit_gun >= 0)
);
