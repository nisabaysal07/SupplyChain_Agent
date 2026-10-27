"""
Tedarikçi veri setini üretir. Tek kaynak: kaynak_veri.py

    python build_dataset.py

Çıktılar (bu klasöre):
    tedarikciler.csv  her parça için tek tedarikçi: menşe, fiyat, sözleşme
    rotalar.csv       her tedarikçinin Türkiye'ye geliş rotası
    parcalar.csv      parçalar: GTİP, vergi oranları, stok
    ulkeler.csv       menşe ülkeler: anlaşma durumu ve vergi çarpanları
    firmalar.csv      üretici firmalar
"""
import csv
import sys

sys.dont_write_bytecode = True
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kaynak_veri as K  # noqa: E402

KLASOR = Path(__file__).resolve().parent

TABLOLAR = {
    "ulkeler.csv": ["ulke_id", "ulke_adi", "anlasma_durumu", "gv_carpani", "igv_carpani"],
    "firmalar.csv": ["firma_id", "firma_adi", "resmi_ad", "merkez_ulke"],
    "parcalar.csv": ["parca_id", "parca_adi", "hs6", "gtip12", "tarife_gv_tercihsiz", "tarife_igv_tercihsiz",
                     "kultur_fonu_orani", "otv_orani", "kdv_orani", "oran_kaynagi",
                     "eldeki_stok", "rezerve_stok", "yeniden_siparis_seviyesi"],
    "tedarikciler.csv": ["tedarikci_id", "parca_id", "firma_id", "mense_ulke_id",
                         "birlestirme_ulke", "perakende_usd", "fiyat_tarihi",
                         "sozlesme_baslangic", "sozlesme_bitis"],
    "rotalar.csv": ["tedarikci_id", "tasima_modu", "cikis_noktasi", "aktarma_noktasi", "varis_noktasi",
                    "transit_gun"],
}


def satirlar():
    parcalar = [[pid, ad, hs6, g12, gv, igv, kf, otv, K.KDV_ORANI, K.ORAN_KAYNAGI, eldeki, rezerve, siparis]
                for pid, ad, hs6, g12, gv, igv, kf, otv, eldeki, rezerve, siparis in K.PARCALAR]
    tedarikciler, rotalar = [], []
    for t in K.TEDARIKCILER:
        tedarikciler.append([
            t["tedarikci_id"], t["parca_id"], t["firma_id"], t["mense_ulke_id"],
            t["birlestirme"], t["fiyat"], t["fiyat_tarihi"], *t["sozlesme"],
        ])
        rotalar.append([t["tedarikci_id"], *t["rota"]])
    return {
        "ulkeler.csv": [list(u) for u in K.ULKELER],
        "firmalar.csv": [list(f) for f in K.FIRMALAR],
        "parcalar.csv": parcalar,
        "tedarikciler.csv": tedarikciler,
        "rotalar.csv": rotalar,
    }


def dogrula(veri):
    def idler(ad):
        return [r[0] for r in veri[ad]]

    for ad, rows in veri.items():
        assert len(idler(ad)) == len(set(idler(ad))), f"{ad}: kimlik tekrar ediyor"
        assert all(len(r) == len(TABLOLAR[ad]) for r in rows), f"{ad}: sütun sayısı"
        assert all(v not in ("", None) for r in rows for v in r), f"{ad}: boş hücre"
    parca, firma, ulke = set(idler("parcalar.csv")), set(idler("firmalar.csv")), set(idler("ulkeler.csv"))
    ted = veri["tedarikciler.csv"]
    assert sorted(r[1] for r in ted) == sorted(parca), "her parçada tam bir tedarikçi olmalı"
    for r in ted:
        assert r[2] in firma and r[3] in ulke, f"tedarikçi {r[0]}: bağlantı hatası"
    assert sorted(idler("rotalar.csv")) == sorted(idler("tedarikciler.csv")), "her tedarikçinin tek rotası olmalı"


def main():
    veri = satirlar()
    dogrula(veri)
    for ad, rows in veri.items():
        # ";" ayırıcı ve UTF-8 BOM: dosya Türkçe Excel'de çift tıklanınca sütunlara ayrılmış açılır
        with open(KLASOR / ad, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(TABLOLAR[ad])
            w.writerows(rows)
    print(" · ".join(f"{ad}: {len(r)} satır" for ad, r in veri.items()))


if __name__ == "__main__":
    main()
