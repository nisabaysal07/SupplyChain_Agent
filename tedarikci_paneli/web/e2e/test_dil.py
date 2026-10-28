"""Arayüz dili: varsayılan İngilizce, istenirse Türkçe; seçim sayfa yenilense de korunur."""

import re

from playwright.sync_api import Page, expect

from conftest import giris_yap, hidrasyonu_bekle


def dil_sec(page: Page, mevcut_etiket: str, dil: str) -> None:
    # Seçicinin erişilebilir adı o anki dilde: "Language" / "Dil"
    page.get_by_role("combobox", name=mevcut_etiket).click()
    page.get_by_role("option", name=dil).click()


def test_varsayilan_dil_ingilizce(page: Page):
    page.goto("/giris")
    expect(page.locator("html")).to_have_attribute("lang", "en")
    expect(page.get_by_role("button", name="Sign in")).to_be_visible()
    expect(page.get_by_text("Supply chain risk dashboard")).to_be_visible()


def test_giris_sayfasinda_turkceye_gecilir_ve_dogrulama_turkce(page: Page):
    page.goto("/giris")
    hidrasyonu_bekle(page)
    dil_sec(page, "Language", "Türkçe")
    expect(page.locator("html")).to_have_attribute("lang", "tr")
    expect(page.get_by_role("button", name="Giriş yap")).to_be_visible()

    page.get_by_label("E-posta").fill("eposta-degil")
    page.get_by_label("Şifre").fill("herhangi")
    page.get_by_role("button", name="Giriş yap").click()
    expect(page.get_by_text("Geçerli bir e-posta girin")).to_be_visible()


def test_panelde_dil_degisir_ve_yenilemede_korunur(oturum: Page):
    expect(oturum.get_by_role("heading", name="Dashboard", exact=True)).to_be_visible()

    dil_sec(oturum, "Language", "Türkçe")
    expect(oturum.get_by_role("heading", name="Kontrol Paneli", exact=True)).to_be_visible()
    expect(oturum.get_by_role("link", name="Tedarikçiler", exact=True).first).to_be_visible()
    expect(oturum.get_by_text("Genel portföy risk skoru")).to_be_visible()

    # Çerezde saklandı: sunucu da Türkçe çizer
    oturum.reload()
    hidrasyonu_bekle(oturum)
    expect(oturum.locator("html")).to_have_attribute("lang", "tr")
    expect(oturum.get_by_role("heading", name="Kontrol Paneli", exact=True)).to_be_visible()

    # Başka sayfada da Türkçe; sonra İngilizceye dönülür
    oturum.get_by_role("link", name="Tedarikçiler", exact=True).first.click()
    expect(oturum.get_by_role("heading", name="Tedarikçiler", exact=True)).to_be_visible()
    expect(oturum.get_by_text(re.compile(r"^\d+ / \d+ tedarikçi$"))).to_be_visible()

    dil_sec(oturum, "Dil", "English")
    expect(oturum.get_by_role("heading", name="Suppliers", exact=True)).to_be_visible()
    expect(oturum.get_by_text(re.compile(r"^\d+ / \d+ suppliers$"))).to_be_visible()


def test_giris_yapinca_secilen_dil_korunur(page: Page, sunucu):
    page.goto("/giris")
    hidrasyonu_bekle(page)
    dil_sec(page, "Language", "Türkçe")
    page.get_by_label("E-posta").fill(sunucu.eposta)
    page.get_by_label("Şifre").fill(sunucu.sifre)
    page.get_by_role("button", name="Giriş yap").click()
    expect(page.get_by_role("heading", name="Kontrol Paneli", exact=True)).to_be_visible()
    # Diğer testler İngilizce bekler; bu test kendi tarayıcı bağlamında çalışır
    dil_sec(page, "Dil", "English")
    expect(page.get_by_role("heading", name="Dashboard", exact=True)).to_be_visible()
