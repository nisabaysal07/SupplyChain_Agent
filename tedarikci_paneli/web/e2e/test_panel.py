"""Giriş yapmış yöneticinin panelde gezinmesi ve olayları görmesi (varsayılan dil: İngilizce)."""

import re

import pytest
from playwright.sync_api import Page, expect

from conftest import hidrasyonu_bekle


@pytest.mark.parametrize(
    ("menu", "yol", "baslik"),
    [
        ("Suppliers", "/tedarikciler", "Suppliers"),
        ("Events", "/olaylar", "Events"),
        ("Data Upload", "/yukleme", "Data Upload"),
        ("Settings", "/ayarlar", "Settings"),
        ("Dashboard", "/", "Dashboard"),
    ],
)
def test_yan_menu_sayfalari_acar(oturum: Page, sunucu, menu, yol, baslik):
    if yol == "/":
        oturum.goto("/ayarlar")
    oturum.get_by_role("link", name=menu, exact=True).first.click()
    expect(oturum).to_have_url(f"{sunucu.url}{yol}")
    expect(oturum.get_by_role("heading", name=baslik, exact=True)).to_be_visible()


def test_model_gonderdigi_olaylar_listelenir(oturum: Page, ornek_olaylar):
    oturum.goto("/olaylar")
    liste = oturum.get_by_role("region", name="Active events")
    expect(liste.get_by_text(re.compile(r"^\d+ active events?$"))).to_be_visible()

    ilk = ornek_olaylar[0]
    expect(liste.get_by_text(ilk["baslik"])).to_be_visible()


def test_olay_secilince_detayi_gosterilir(oturum: Page, ornek_olaylar):
    oturum.goto("/olaylar")
    hidrasyonu_bekle(oturum)
    liste = oturum.get_by_role("region", name="Active events")
    detay = oturum.get_by_role("region", name="Event details")

    # Bitiş tarihi olan örnekler zamanla süresi dolup listeden düşer; süresizleri seç
    suresizler = [o for o in ornek_olaylar if not o.get("bitisTarihi")]
    assert len(suresizler) >= 2, "En az iki süresiz örnek olay gerekli"
    for olay in suresizler[:2]:
        liste.get_by_role("button", name=re.compile(f"^{re.escape(olay['baslik'])}")).click()
        expect(detay.get_by_role("heading", name=olay["baslik"])).to_be_visible()
        expect(detay.get_by_text("Sample event")).to_be_visible()
