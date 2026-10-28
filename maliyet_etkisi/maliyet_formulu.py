"""
Görev 3.2 — Maliyet etkisi formülü.

Bir olayın KurguTek'e etkisini hesaplar: birim ve yıllık maliyet farkı, bilgisayar başına fark,
üretim durması. Veri tabloları yalnızca okunur; klasör sırasıyla MALIYET_VERI_KLASORU ortam
değişkeninden, bu dosyanın yanındaki data/raw/ klasöründen, ../tedarikci_paneli'den ya da
../TedarikciSetiYeni'den alınır.

    from maliyet_formulu import analiz_et, ajan_analiz
    analiz_et({"olay_turu": "vergi_degisikligi", "kapsam": {"mense_ulke": ["Çin"], "parca": ["Güç kaynağı"]},
               "parametre": {"vergi": "igv", "yeni_oran": 0.20}, "yururluk": "2026-11-01"})
    ajan_analiz(ajan_json)   # ajanın çıktısı (OUTPUT_FORMAT.md 1.1; metin ya da sözlük) → sonuç listesi
    stok_raporu()            # olaydan bağımsız, bütün parçaların stok durumu

Olay türleri ve parametreleri:
    vergi_degisikligi   vergi: gv | igv | kultur_fonu | otv | kdv ; yeni_oran (0.20) veya oran_degisimi (+0.05)
    anlasma_degisikligi ulke: "Güney Kore" ; anlasma_durumu: 0 | 1
    lojistik_gecikme    gecikme_gun: 18 (boş = süre belirsiz)
Olayda isteğe bağlı: yururluk (ISO tarih; yoksa bugün), taslak (True = henüz yürürlükte değil),
belirsiz (True = haber net değil).
Kapsam (isteğe bağlı listeler): tedarikci_id, parca, firma, mense_ulke, tasima_modu,
cikis_noktasi, aktarma_noktasi, varis_noktasi, nokta (rotadaki herhangi bir nokta).

Formüller (bir adet için):
    gümrük kıymeti = birim fiyat
    GV, İGV, Kültür Fonu = kıymet × (parçanın oranı × ülkenin çarpanı; Kültür Fonu çarpansız)
    ÖTV = (kıymet + GV + İGV + Kültür Fonu) × ÖTV oranı
    birim maliyet = birim fiyat + vergiler (KDV indirilebildiği için eklenmez; KDV değişikliği 0 $)
    yıllık fark = birim maliyet farkı × yıllık adet ; bilgisayar başına fark = yıllık fark ÷ yıllık bilgisayar
    stok günü = (eldeki − rezerve) ÷ günlük kullanım ; durma günü = bekleme − stok günü (eksiyse 0)
    stok durumu: kalan = stok günü − gecikme (olay yoksa 0) ; kalan < yol + gümrük → yetersiz ;
        kalan ≤ sipariş seviyesi günü → sınıra yakın ; yoksa yeterli (stok_uyarisi = durum yeterli değil)
Anlaşmalı ülkede sanayi ürünlerinde GV ve İGV çarpanı 0'dır (ulkeler.csv ile aynı kural).
"""
import copy
import csv
import json
import os
from datetime import date
from pathlib import Path

# Şirket ayarları (veri tablolarında yok): yılda 10.000 bilgisayar; ekran kartı ve monitör modellerin yarısında
YILLIK_PC = 10_000
PARCA_ADET_ORANI = {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 0.5, 6: 1.0, 7: 1.0, 8: 1.0, 9: 0.5}
YIL_GUN = 365
GUMRUK_GUN = 1   # veri tablosundaki yeniden sipariş seviyesi kuralıyla aynı (yol + gümrük 1 gün + 14 gün)
STOK_DURUMLARI = ("yetersiz", "sinira_yakin", "yeterli")
# Çıktı metinleri (mesaj, neden, uyarılar) İngilizcedir; rapor İngilizce yazılır.
STOK_DURUM_ADI = {"yetersiz": "insufficient stock", "sinira_yakin": "stock near reorder level",
                  "yeterli": "sufficient stock"}

VERGI_SUTUNU = {"gv": "tarife_gv_tercihsiz", "igv": "tarife_igv_tercihsiz",
                "kultur_fonu": "kultur_fonu_orani", "otv": "otv_orani"}
INDIRILEBILIR_VERGILER = ("kdv",)   # maliyete girmez
OLAY_TURLERI = ("vergi_degisikligi", "anlasma_degisikligi", "lojistik_gecikme", "fiyat_degisikligi")


def _veri_klasoru():
    if os.environ.get("MALIYET_VERI_KLASORU"):
        return Path(os.environ["MALIYET_VERI_KLASORU"])
    burasi = Path(__file__).resolve().parent
    adaylar = [burasi / "data" / "raw", burasi.parent / "tedarikci_paneli", burasi.parent / "TedarikciSetiYeni"]
    return next((k for k in adaylar if (k / "tedarikciler.csv").exists()), adaylar[-1])


class Veri:
    """Veri tablolarını kimlikleriyle yükler; olaylar bir kopya üzerinde uygulanır."""

    def __init__(self, klasor=None):
        klasor = Path(klasor) if klasor else _veri_klasoru()

        def oku(ad, anahtar):
            with open(klasor / f"{ad}.csv", encoding="utf-8-sig") as f:
                return {r[anahtar]: r for r in csv.DictReader(f, delimiter=";")}

        self.tedarikci = oku("tedarikciler", "tedarikci_id")
        self.rota = oku("rotalar", "tedarikci_id")
        self.parca = oku("parcalar", "parca_id")
        self.ulke = oku("ulkeler", "ulke_id")
        self.firma = oku("firmalar", "firma_id")
        self.ozel_oran = {}   # (tedarikci_id, vergi) → olayla değişen tercihsiz oran
        self.uygulanan_oran = {}

    def kopya(self):
        return copy.deepcopy(self)

    def bilgi(self, tid):
        t = self.tedarikci[tid]
        return {"parca": self.parca[t["parca_id"]], "firma": self.firma[t["firma_id"]],
                "ulke": self.ulke[t["mense_ulke_id"]], "rota": self.rota[tid]}

    def ulke_bul(self, ad):
        return next((u for u in self.ulke.values() if u["ulke_adi"].casefold() == str(ad).casefold()), None)


# --- formüller ---------------------------------------------------------------------------

def yillik_adet(v, tid):
    pid = v.tedarikci[tid]["parca_id"]
    if int(pid) not in PARCA_ADET_ORANI:
        raise ValueError(f"annual quantity unknown for {v.parca[pid]['parca_adi']}")
    return round(YILLIK_PC * PARCA_ADET_ORANI[int(pid)])


def gunluk_kullanim(v, tid):
    return yillik_adet(v, tid) / YIL_GUN


def birim_fiyat(v, tid):
    return float(v.tedarikci[tid]["perakende_usd"])


def vergi_oranlari(v, tid):
    b = v.bilgi(tid)
    oran = {k: float(v.ozel_oran.get((tid, k), b["parca"][s])) for k, s in VERGI_SUTUNU.items()}
    oran["gv"] *= float(b["ulke"]["gv_carpani"])
    oran["igv"] *= float(b["ulke"]["igv_carpani"])
    oran.update({k: x for (t, k), x in v.uygulanan_oran.items() if t == tid})
    return oran


def birim_vergi_detay(v, tid):
    oran, kiymet = vergi_oranlari(v, tid), birim_fiyat(v, tid)
    d = {k: kiymet * oran[k] for k in ("gv", "igv", "kultur_fonu")}
    d["otv"] = (kiymet + sum(d.values())) * oran["otv"]
    return d


def birim_maliyet(v, tid):
    return birim_fiyat(v, tid) + sum(birim_vergi_detay(v, tid).values())


def yillik_maliyet(v, tid):
    return birim_maliyet(v, tid) * yillik_adet(v, tid)


def pc_basi_maliyet(v):
    return sum(yillik_maliyet(v, tid) for tid in v.tedarikci) / YILLIK_PC


def stok_gunu(v, tid):
    p = v.parca[v.tedarikci[tid]["parca_id"]]
    return (int(p["eldeki_stok"]) - int(p["rezerve_stok"])) / gunluk_kullanim(v, tid)


def stok_durumu(v, tid, bekleme=None):
    """yetersiz | sinira_yakin | yeterli. Tek kural; gecikme arttıkça durum yalnızca kötüleşebilir.

    kalan = stok günü − gecikme (olay yoksa ya da süre belirsizse gecikme = 0)
    kalan < yol + gümrük → yetersiz (yeni sipariş stok bitmeden gelmez) ;
    kalan ≤ yeniden sipariş seviyesi günü → sınıra yakın ; diğer durumlar → yeterli"""
    kalan = stok_gunu(v, tid) - (bekleme or 0.0)
    yenileme = float(v.rota[tid]["transit_gun"]) + GUMRUK_GUN
    esik = int(v.parca[v.tedarikci[tid]["parca_id"]]["yeniden_siparis_seviyesi"]) / gunluk_kullanim(v, tid)
    return "yetersiz" if kalan < yenileme else "sinira_yakin" if kalan <= esik else "yeterli"


def _stok_ozeti(durumlar):
    sayilar = {d: durumlar.count(d) for d in STOK_DURUMLARI}
    return sayilar, ", ".join(f"{n} part{'s' if n > 1 else ''} with {STOK_DURUM_ADI[d]}"
                              for d, n in sayilar.items() if n)


def stok_raporu(v=None):
    """Olaydan bağımsız, bütün tedarikçilerin bugünkü stok durumu."""
    v = v or Veri()
    satirlar = [{"tedarikci_id": tid, "parca": v.bilgi(tid)["parca"]["parca_adi"],
                 "stok_gunu": round(stok_gunu(v, tid), 1), "stok_durumu": stok_durumu(v, tid)}
                for tid in v.tedarikci]
    sayilar, ozet = _stok_ozeti([s["stok_durumu"] for s in satirlar])
    return {"stok_durum_sayilari": sayilar, "mesaj": f"Stock: {ozet}.", "tedarikciler": satirlar}


# --- olayın kapsamı ve uygulanması -------------------------------------------------------------

def _esit(deger, liste):
    return str(deger).casefold() in {str(x).casefold() for x in liste}


def _bos(x):
    return x is None or (isinstance(x, str) and not x.strip())


def _sayi(x):
    """1029950 → '1,029,950'"""
    return f"{x:,.0f}"


def _usd(x):
    """1029950 → '$1,029,950' ; -5000 → '-$5,000'"""
    s = f"${_sayi(abs(x))}"
    return f"-{s}" if round(x) < 0 else s


def kapsamda(v, tid, kapsam):
    b = v.bilgi(tid)
    alanlar = {"tedarikci_id": tid, "parca": b["parca"]["parca_adi"], "firma": b["firma"]["firma_adi"],
               "mense_ulke": b["ulke"]["ulke_adi"], "tasima_modu": b["rota"]["tasima_modu"],
               "cikis_noktasi": b["rota"]["cikis_noktasi"], "aktarma_noktasi": b["rota"]["aktarma_noktasi"],
               "varis_noktasi": b["rota"]["varis_noktasi"]}
    for alan, liste in (kapsam or {}).items():
        if alan == "nokta":
            if not any(_esit(alanlar[n], liste) for n in ("cikis_noktasi", "aktarma_noktasi", "varis_noktasi")):
                return False, "route does not pass through these points"
        elif alan not in alanlar:
            return False, f"unknown scope field: {alan}"
        elif not _esit(alanlar[alan], liste):
            return False, f"{alan} = {alanlar[alan]} (out of scope)"
    return True, ""


def _vergi(v, eslesen, p):
    vergi = p.get("vergi")
    if _bos(vergi):
        raise ValueError("tax type is unclear")
    if vergi in INDIRILEBILIR_VERGILER:   # maliyete girmez; sonuç 0 $ olarak raporlanır
        return
    if vergi not in VERGI_SUTUNU:
        raise ValueError(f"unrecognized tax type: {vergi} (expected gv, igv, kultur_fonu, otv or kdv)")
    if _bos(p.get("yeni_oran")) and _bos(p.get("oran_degisimi")):
        raise ValueError("new rate not specified")
    ulkeye_ozel = bool(p.get("ulkeye_ozel")) and vergi in ("gv", "igv")
    for tid in eslesen:
        eski = (vergi_oranlari(v, tid)[vergi] if ulkeye_ozel else
                float(v.ozel_oran.get((tid, vergi), v.parca[v.tedarikci[tid]["parca_id"]][VERGI_SUTUNU[vergi]])))
        yeni = float(p["yeni_oran"]) if not _bos(p.get("yeni_oran")) else eski + float(p["oran_degisimi"])
        if not 0 <= yeni <= 5:
            raise ValueError(f"tax rate must be between 0 and 5, got {yeni}")
        (v.uygulanan_oran if ulkeye_ozel else v.ozel_oran)[(tid, vergi)] = yeni


def _anlasma(v, eslesen, p):
    u = v.ulke_bul(p.get("ulke", ""))
    if u is None or str(p.get("anlasma_durumu")) not in ("0", "1"):
        raise ValueError("parametre.ulke (a country in the countries table) and parametre.anlasma_durumu (0/1) "
                         "are required")
    u["anlasma_durumu"] = str(p["anlasma_durumu"])
    u["gv_carpani"] = u["igv_carpani"] = "0.0" if u["anlasma_durumu"] == "1" else "1.0"


def _fiyat(v, eslesen, p):
    if _bos(p.get("degisim_orani")):
        raise ValueError("price change not specified")
    oran = float(p["degisim_orani"])
    if oran <= -1:
        raise ValueError(f"price change must be greater than -100%, got {oran * 100:g}%")
    for tid in eslesen:
        v.tedarikci[tid]["perakende_usd"] = str(birim_fiyat(v, tid) * (1 + oran))


UYGULA = {"vergi_degisikligi": _vergi, "anlasma_degisikligi": _anlasma, "fiyat_degisikligi": _fiyat}


# --- maliyet etkisi ------------------------------------------------------------------------------

def analiz_et(olay, v=None, bugun=None):
    """Olayın maliyet etkisini döner. Tanınmayan olay ya da hatalı parametrede rakam üretmez."""
    v = v or Veri()
    bugun = bugun or date.today()
    tur, p, kapsam = olay.get("olay_turu"), olay.get("parametre") or {}, dict(olay.get("kapsam") or {})
    taslak, belirsiz = bool(olay.get("taslak")), bool(olay.get("belirsiz"))
    temel = {"olay_id": olay.get("olay_id"), "olay_turu": tur, "taslak": taslak, "belirsiz": belirsiz}
    if tur not in OLAY_TURLERI:
        return {**temel, "durum": "hesaplanamadi", "neden": f"unrecognized event type: {tur}"}
    if tur == "anlasma_degisikligi" and "ulke" in p:
        kapsam.setdefault("mense_ulke", [p["ulke"]])

    eslesen, disarida = [], []
    for tid in v.tedarikci:
        ok, neden = kapsamda(v, tid, kapsam)
        (eslesen if ok else disarida).append(tid if ok else {"tedarikci_id": tid, "neden": neden})

    sonra = v.kopya()
    try:
        yururluk = date.fromisoformat(olay["yururluk"]) if not _bos(olay.get("yururluk")) else None
        if tur in UYGULA:
            UYGULA[tur](sonra, eslesen, p)
        bekleme = None
        if tur == "lojistik_gecikme" and not _bos(p.get("gecikme_gun")):
            bekleme = float(p["gecikme_gun"])
            if bekleme < 0:
                raise ValueError("number of days cannot be negative")
    except (KeyError, ValueError, TypeError) as e:
        return {**temel, "durum": "hesaplanamadi", "neden": str(e)}
    sure_belirsiz = tur == "lojistik_gecikme" and bekleme is None
    indirilebilir = tur == "vergi_degisikligi" and p.get("vergi") in INDIRILEBILIR_VERGILER
    yururluk_varsayildi = yururluk is None
    yururluk = yururluk or bugun
    yil_sonu = date(yururluk.year, 12, 31)
    kalan = max(0, (yil_sonu - yururluk).days + 1)

    etkilenen = []
    for tid in eslesen:
        n = yillik_adet(v, tid)
        once_b, sonra_b = birim_maliyet(v, tid), birim_maliyet(sonra, tid)
        fark_y = (sonra_b - once_b) * n
        sg = stok_gunu(v, tid)
        durma = None if sure_belirsiz else max(0.0, (bekleme or 0.0) - sg)
        etkilenen.append({
            "tedarikci_id": tid, "yillik_adet": n,
            "birim_maliyet_once": round(once_b, 2), "birim_maliyet_sonra": round(sonra_b, 2),
            "birim_vergi_sonra": {k: round(x, 2) for k, x in birim_vergi_detay(sonra, tid).items()},
            "birim_fark": round(sonra_b - once_b, 2), "yillik_fark": round(fark_y),
            "etki_baslangic": yururluk.isoformat(), "yil_sonuna_kadar_fark": round(fark_y * kalan / YIL_GUN),
            "pc_basi_fark": round(fark_y / YILLIK_PC, 2), "stok_gunu": round(sg, 1),
            "durma_gun": None if durma is None else round(durma, 1),
            "uretilemeyen_pc": None if durma is None else round(durma * gunluk_kullanim(v, tid)),
            # gecikme süresi bilinmiyorsa ya da olay gecikme değilse bugünkü stok durumu
            "stok_durumu": stok_durumu(v, tid, bekleme if tur == "lojistik_gecikme" else None),
        })
        etkilenen[-1]["stok_uyarisi"] = etkilenen[-1]["stok_durumu"] != "yeterli"

    yillik = sum(s["yillik_fark"] for s in etkilenen)
    yil_sonuna = sum(s["yil_sonuna_kadar_fark"] for s in etkilenen)
    toplam_once = sum(yillik_maliyet(v, tid) for tid in v.tedarikci)
    yon = "etkilenen_yok" if not eslesen else "artis" if yillik > 0 else "azalis" if yillik < 0 else "parasal_etki_yok"
    durmalar = [s["durma_gun"] for s in etkilenen if s["durma_gun"] is not None]
    en_kisa_stok = min((s["stok_gunu"] for s in etkilenen), default=None)
    stok_sayilari, stok_ozeti = _stok_ozeti([s["stok_durumu"] for s in etkilenen])
    en_kotu_stok = next((d for d in STOK_DURUMLARI if stok_sayilari[d]), None)

    if not eslesen:
        mesaj = "No suppliers in scope; no cost impact."
    elif indirilebilir:
        mesaj = "VAT is deductible, so there is no cost impact ($0)."
    elif sure_belirsiz:
        mesaj = f"Duration unknown; stock lasts {en_kisa_stok:.0f} days."
    elif tur == "lojistik_gecikme":
        mesaj = (f"Production stops for {max(durmalar):.0f} days; "
                 f"{_sayi(max(s['uretilemeyen_pc'] for s in etkilenen))} computers cannot be built."
                 if max(durmalar) > 0 else
                 f"Stock covers the delay (shortest {en_kisa_stok:.0f} days); production continues.")
    else:
        mesaj = (f"Annual {_usd(yillik)}, {_usd(yil_sonuna)} until year-end, "
                 f"{_usd(yillik / YILLIK_PC)} per computer.")
    if eslesen:
        mesaj += f" Stock: {stok_ozeti}."
    if yururluk_varsayildi and tur != "lojistik_gecikme" and yillik:
        mesaj += " No effective date given; impact counted from today."
    if taslak:
        mesaj = "If the draft takes effect: " + mesaj
    elif belirsiz:
        mesaj = "News is unconfirmed; if accurate: " + mesaj

    return {
        **temel, "durum": "hesaplandi", "yururluk": yururluk.isoformat(), "yururluk_varsayildi": yururluk_varsayildi,
        "yon": yon, "sure_belirsiz": sure_belirsiz, "mesaj": mesaj,
        "toplam": {
            "yillik_fark": yillik,
            "yil_sonuna_kadar_fark": yil_sonuna,
            "pc_basi_fark": round(yillik / YILLIK_PC, 2),
            "pc_basi_maliyet_once": round(pc_basi_maliyet(v), 2),
            "pc_basi_maliyet_sonra": round(pc_basi_maliyet(v) + yillik / YILLIK_PC, 2),
            "yuzde": round(yillik / toplam_once * 100, 2) if toplam_once else 0.0,
            "en_kisa_stok_gunu": en_kisa_stok,
            "en_uzun_durma_gun": max(durmalar, default=None if sure_belirsiz else 0),
            "uretilemeyen_pc": None if sure_belirsiz else max((s["uretilemeyen_pc"] for s in etkilenen), default=0),
            "stok_durumu": en_kotu_stok,   # etkilenenler içindeki en kötü durum
            "stok_durum_sayilari": stok_sayilari,
            "stok_uyarisi": any(s["stok_uyarisi"] for s in etkilenen),
        },
        "etkilenenler": etkilenen, "etkilenmeyenler": disarida,
    }


# --- ajan köprüsü (OUTPUT_FORMAT.md, sürüm 1.1) --------------------------------------------------------
# Dosya: {"schema_version", "run", "results": [...]}. Kayıtta üst düzey: news_id, is_relevant, event_type,
# affected_supplier_ids; analysis içinde: status, rate_type, old_rate_pct, new_rate_pct, effective_date,
# expected_delay_days. Oranlar yüzde gelir (20 = %20).

AJAN_SURUMLERI = ("1.1", "1.3")
AJAN_OLAY_TURU = {"tariff_increase": "vergi_degisikligi", "tariff_decrease": "vergi_degisikligi",
                  "transport_disruption": "lojistik_gecikme", "trade_restriction": "lojistik_gecikme",
                  "price_change": "fiyat_degisikligi"}   # other, not_relevant atlanır
AJAN_VERGI = {"gv": "gv", "igv": "igv", "kultur_fonu": "kultur_fonu", "otv": "otv", "kdv": "kdv"}
# analysis.status: enacted = kesin, ongoing_event = süren olay, proposed = taslak, unclear = haber net değil


def ajan_olayi_cevir(kayit):
    """Ajanın tek kaydını analiz_et'in olayına çevirir; atlanacak kayıtta None, hatalıda {"hata": ...} döner.

    Atlananlar: is_relevant false ya da null (filtre hatası, ajan tekrar işler), analysis null (ilgisiz ya da
    analiz hatası) ve maliyetle hesaplanmayan türler."""
    a = kayit.get("analysis")
    if kayit.get("is_relevant") is not True or not isinstance(a, dict):
        return None
    tur = AJAN_OLAY_TURU.get(str(kayit.get("event_type") or "").strip().lower())
    if tur is None:
        return None
    durum = str(a.get("status") or "").strip().lower()
    olay = {"olay_id": kayit.get("news_id"), "olay_turu": tur,
            "kapsam": {"tedarikci_id": [str(t) for t in (kayit.get("affected_supplier_ids") or [])]},
            "yururluk": a.get("effective_date"), "taslak": durum == "proposed", "belirsiz": durum == "unclear",
            "parametre": {}}
    if tur == "lojistik_gecikme":
        olay["parametre"]["gecikme_gun"] = a.get("expected_delay_days")
        return olay
    if tur == "fiyat_degisikligi":
        if _bos(a.get("price_change_pct")):
            return {"hata": "price change not specified", **olay}
        olay["parametre"]["degisim_orani"] = float(a["price_change_pct"]) / 100
        return olay
    rate_type = a.get("rate_type")
    if _bos(rate_type):
        return {"hata": "tax type is unclear", **olay}
    vergi = AJAN_VERGI.get(str(rate_type).strip().lower())
    if vergi is None:
        return {"hata": f"unrecognized tax type: {rate_type}", **olay}
    olay["parametre"]["vergi"] = vergi
    if vergi in INDIRILEBILIR_VERGILER:
        return olay
    if _bos(a.get("new_rate_pct")):
        return {"hata": "new rate not specified", **olay}
    olay["parametre"]["yeni_oran"] = float(a["new_rate_pct"]) / 100
    if a.get("ulkeye_ozel"):
        olay["parametre"]["ulkeye_ozel"] = True
    if not _bos(a.get("old_rate_pct")):
        olay["eski_oran_haber"] = float(a["old_rate_pct"]) / 100
    return olay


def _eski_oran_uyarisi(v, olay):
    """Haberdeki eski oran tablodaki tercihsiz oranla uyuşmuyorsa uyarı (hesap tablodaki orandan yapılır)."""
    eski, vergi = olay.get("eski_oran_haber"), olay["parametre"].get("vergi")
    if eski is None or vergi not in VERGI_SUTUNU:
        return []
    ulkeye_ozel = olay["parametre"].get("ulkeye_ozel")
    tablo = lambda tid: (vergi_oranlari(v, tid)[vergi] if ulkeye_ozel else
                         float(v.parca[v.tedarikci[tid]["parca_id"]][VERGI_SUTUNU[vergi]]))
    farkli = sorted({tid for tid in olay["kapsam"]["tedarikci_id"] if tid in v.tedarikci and
                     abs(tablo(tid) - eski) > 1e-9})
    return [f"The old rate in the news ({eski * 100:g}%) differs from the table rate (supplier "
            f"{', '.join(farkli)}); the calculation uses the table rate."] if farkli else []


def _sta_uyarisi(v, olay):
    if not olay["parametre"].get("ulkeye_ozel") or olay["parametre"].get("vergi") not in ("gv", "igv"):
        return []
    return [f"The rate is applied to a free-trade-agreement country ({v.bilgi(tid)['ulke']['ulke_adi']}) for supplier "
            f"{tid}; check that the news names this country."
            for tid in olay["kapsam"]["tedarikci_id"]
            if tid in v.tedarikci and v.bilgi(tid)["ulke"]["anlasma_durumu"] == "1"]


def ajan_analiz(ajan_cikti, v=None, bugun=None):
    """Ajanın JSON çıktısını (dosya içeriği metni ya da sözlüğü; tek kayıt ya da kayıt listesi de olur) analiz eder.
    Atlanan kayıtlar listede yer almaz."""
    if isinstance(ajan_cikti, (str, bytes)):
        ajan_cikti = json.loads(ajan_cikti)
    genel_uyari = []
    if isinstance(ajan_cikti, dict) and "results" in ajan_cikti:
        surum = str(ajan_cikti.get("schema_version"))
        if surum not in AJAN_SURUMLERI:
            genel_uyari.append(f"Agent output schema version is {surum}; the bridge was written for "
                               f"{', '.join(AJAN_SURUMLERI)}.")
        if (ajan_cikti.get("run") or {}).get("mock"):
            genel_uyari.append("Mock run (run.mock): results are not real, do not use them.")
        ajan_cikti = ajan_cikti["results"] or []
    elif isinstance(ajan_cikti, dict):
        ajan_cikti = [ajan_cikti]
    v = v or Veri()
    sonuclar = []
    for kayit in ajan_cikti:
        try:
            olay = ajan_olayi_cevir(kayit)
        except (ValueError, TypeError) as e:
            tur = str(kayit.get("event_type"))
            olay = {"hata": f"invalid value in agent record: {e}", "olay_id": kayit.get("news_id"),
                    "olay_turu": AJAN_OLAY_TURU.get(tur, tur), "taslak": False, "belirsiz": False}
        if olay is None:
            continue
        try:
            if "hata" in olay:
                raise ValueError(olay["hata"])
            sonuc = analiz_et(olay, v, bugun)
            sonuc["uyarilar"] = genel_uyari + _eski_oran_uyarisi(v, olay) + _sta_uyarisi(v, olay)
        except (KeyError, ValueError, TypeError, ZeroDivisionError) as e:
            sonuc = {"olay_id": olay["olay_id"], "olay_turu": olay["olay_turu"], "taslak": olay["taslak"],
                     "belirsiz": olay["belirsiz"], "durum": "hesaplanamadi", "neden": f"missing value: {e.args[0]}" if isinstance(e, KeyError) else str(e),
                     "uyarilar": genel_uyari}
        sonuclar.append(sonuc)
    return sonuclar


# --- veritabanı köprüsü ----------------------------------------------------------------------------

PUAN_ARALIKLARI = ((80, "enacted"), (66, "proposed"))
ANALIZ_SORGUSU = """
    SELECT * FROM (
        SELECT DISTINCT ON (aa.article_id) aa.id, aa.is_relevant, aa.impact_score, aa.event_type, aa.rate_type,
               aa.old_rate_pct, aa.new_rate_pct, aa.expected_delay_days,
               (a.effective_date AT TIME ZONE 'Europe/Istanbul')::date
        FROM article_analyses aa JOIN articles a ON a.id = aa.article_id
        ORDER BY aa.article_id, aa.scan_log_id DESC) son
    ORDER BY id"""
ETKI_SORGUSU = "SELECT article_analysis_id, item_id, country_id FROM article_impacts"
SIRKET_SORGUSU = """
    SELECT si.item_id, i.name, s.id, s.name, co.id, co.name_tr, co.has_trade_agreement, c.unit_price, c.currency,
           t.gv_rate, t.igv_rate, i.kultur_fonu_rate, i.otv_rate, inv.on_hand, inv.reserved, inv.reorder_point,
           sh.transport_mode, le.name, ld.name, sh.expected_transit_days
    FROM supplier_items si
    JOIN items i ON i.id = si.item_id
    JOIN suppliers s ON s.id = si.supplier_id
    JOIN countries co ON co.id = si.assembly_country_id
    LEFT JOIN LATERAL (SELECT id, unit_price, currency FROM contracts
                       WHERE supplier_item_id = si.id AND is_active ORDER BY start_date DESC LIMIT 1) c ON true
    LEFT JOIN LATERAL (SELECT gv_rate, igv_rate FROM tariffs
                       WHERE item_id = si.item_id AND country_id = si.assembly_country_id AND valid_from <= current_date
                         AND (valid_to IS NULL OR valid_to > current_date)
                       ORDER BY valid_from DESC LIMIT 1) t ON true
    LEFT JOIN inventory inv ON inv.supplier_item_id = si.id
    LEFT JOIN LATERAL (SELECT * FROM shipments WHERE contract_id = c.id ORDER BY id DESC LIMIT 1) sh ON true
    LEFT JOIN locations le ON le.id = sh.exit_location_id
    LEFT JOIN locations ld ON ld.id = sh.destination_location_id
    ORDER BY si.item_id"""
TASIMA_MODU = {"sea": "deniz", "air": "hava", "road": "kara"}


def puan_durumu(puan):
    return next((d for alt, d in PUAN_ARALIKLARI if puan is not None and puan >= alt), "unclear")


def baglan(env=Path(__file__).resolve().parent.parent / ".env"):
    import psycopg
    ayar = dict(s.strip().split("=", 1) for s in env.read_text(encoding="utf-8").splitlines()
                if "=" in s and not s.lstrip().startswith("#"))
    ayar.update({k: os.environ[k] for k in ("POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USER", "POSTGRES_PASSWORD",
                                            "POSTGRES_DB") if k in os.environ})
    return psycopg.connect(host=ayar.get("POSTGRES_HOST", "localhost"), port=ayar.get("POSTGRES_PORT", 5432),
                           user=ayar["POSTGRES_USER"], password=ayar["POSTGRES_PASSWORD"], dbname=ayar["POSTGRES_DB"])


def veritabani_kayitlari(baglanti):
    with baglanti.cursor() as c:
        c.execute(ETKI_SORGUSU)
        etkiler = c.fetchall()
        c.execute(ANALIZ_SORGUSU)
        analizler = c.fetchall()
    kayitlar = []
    for aid, ilgili, puan, tur, rate, eski, yeni, gecikme, yururluk in analizler:
        satirlar = [(i, u) for a, i, u in etkiler if a == aid]
        kayitlar.append({
            "news_id": aid, "is_relevant": ilgili, "event_type": tur,
            "affected_supplier_ids": sorted({str(i) for i, _ in satirlar if i is not None}, key=int),
            "analysis": {"status": puan_durumu(puan), "rate_type": rate, "old_rate_pct": eski, "new_rate_pct": yeni,
                         "expected_delay_days": gecikme, "effective_date": yururluk.isoformat() if yururluk else None,
                         "ulkeye_ozel": any(u is not None for _, u in satirlar)}})
    return kayitlar


def veritabani_verisi(baglanti):
    with baglanti.cursor() as c:
        c.execute(SIRKET_SORGUSU)
        satirlar = c.fetchall()
    v = object.__new__(Veri)
    v.tedarikci, v.rota, v.parca, v.ulke, v.firma, v.ozel_oran, v.uygulanan_oran = {}, {}, {}, {}, {}, {}, {}
    for (item, parca_adi, fid, firma_adi, uid, ulke_adi, anlasma, fiyat, para, gv, igv, kf, otv,
         eldeki, rezerve, siparis, mod, cikis, varis, transit) in satirlar:
        tid, fid, uid = str(item), str(fid), str(uid)
        if tid in v.tedarikci:
            raise ValueError(f"{parca_adi} has more than one supplier; the formula expects one supplier per part")
        eksik = [ad for ad, x in (("unit price", fiyat), ("tariff", gv), ("inventory", eldeki),
                                  ("reorder point", siparis), ("shipment", transit)) if x is None]
        if eksik:
            raise ValueError(f"missing company data for {parca_adi}: {', '.join(eksik)}")
        if para != "USD":
            raise ValueError(f"contract currency for {parca_adi} is {para}; the formula expects USD")
        carpan = "0.0" if anlasma else "1.0"
        v.tedarikci[tid] = {"tedarikci_id": tid, "parca_id": tid, "firma_id": fid, "mense_ulke_id": uid,
                            "perakende_usd": str(fiyat)}
        v.rota[tid] = {"tedarikci_id": tid, "tasima_modu": TASIMA_MODU.get(mod, mod), "cikis_noktasi": cikis,
                       "aktarma_noktasi": "Aktarma yok", "varis_noktasi": varis, "transit_gun": str(transit)}
        v.parca[tid] = {"parca_id": tid, "parca_adi": parca_adi, "tarife_gv_tercihsiz": str(gv / 100),
                        "tarife_igv_tercihsiz": str(igv / 100), "kultur_fonu_orani": str(kf / 100),
                        "otv_orani": str((otv or 0) / 100), "eldeki_stok": str(int(eldeki)),
                        "rezerve_stok": str(int(rezerve)), "yeniden_siparis_seviyesi": str(int(siparis))}
        v.ulke[uid] = {"ulke_id": uid, "ulke_adi": ulke_adi, "anlasma_durumu": "1" if anlasma else "0",
                       "gv_carpani": carpan, "igv_carpani": carpan}
        v.firma[fid] = {"firma_id": fid, "firma_adi": firma_adi}
    return v


def veritabani_analiz(baglanti, v=None, bugun=None):
    return ajan_analiz(veritabani_kayitlari(baglanti), v or veritabani_verisi(baglanti), bugun)


SONUC_SORGUSU = """
    INSERT INTO cost_impacts (article_analysis_id, status, calc_type, direction, annual_diff_usd, year_end_diff_usd,
                              per_pc_diff_usd, cost_share_pct, stock_status, stop_days, unbuilt_pc, duration_unknown,
                              is_draft, is_unconfirmed, affected_item_ids, message, reason, warnings)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (article_analysis_id) DO UPDATE SET
        status = EXCLUDED.status, calc_type = EXCLUDED.calc_type, direction = EXCLUDED.direction,
        annual_diff_usd = EXCLUDED.annual_diff_usd, year_end_diff_usd = EXCLUDED.year_end_diff_usd,
        per_pc_diff_usd = EXCLUDED.per_pc_diff_usd, cost_share_pct = EXCLUDED.cost_share_pct,
        stock_status = EXCLUDED.stock_status, stop_days = EXCLUDED.stop_days, unbuilt_pc = EXCLUDED.unbuilt_pc,
        duration_unknown = EXCLUDED.duration_unknown, is_draft = EXCLUDED.is_draft,
        is_unconfirmed = EXCLUDED.is_unconfirmed, affected_item_ids = EXCLUDED.affected_item_ids,
        message = EXCLUDED.message, reason = EXCLUDED.reason, warnings = EXCLUDED.warnings, calculated_at = now()"""


def sonuclari_yaz(baglanti, sonuclar):
    satirlar = []
    for s in sonuclar:
        t = s.get("toplam") or {}
        satirlar.append((s["olay_id"], s["durum"], s["olay_turu"], s.get("yon"), t.get("yillik_fark"),
                         t.get("yil_sonuna_kadar_fark"), t.get("pc_basi_fark"), t.get("yuzde"), t.get("stok_durumu"),
                         t.get("en_uzun_durma_gun"), t.get("uretilemeyen_pc"), s.get("sure_belirsiz"), s["taslak"],
                         s["belirsiz"], [int(e["tedarikci_id"]) for e in s.get("etkilenenler", [])], s.get("mesaj"),
                         s.get("neden"), s["uyarilar"]))
    with baglanti.cursor() as c:
        c.executemany(SONUC_SORGUSU, satirlar)
    baglanti.commit()
    return len(satirlar)
