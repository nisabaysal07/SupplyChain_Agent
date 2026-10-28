"""Giriş, yönlendirme ve oturum kapatma akışları (varsayılan dil: İngilizce)."""

import re

from playwright.sync_api import Page, expect

from conftest import giris_yap


def test_giris_yapmadan_korunan_sayfa_giris_sayfasina_yonlendirir(page: Page):
    page.goto("/olaylar")
    expect(page).to_have_url(re.compile(r"/giris\?yonlendir=(/|%2F)olaylar$"))
    expect(page.get_by_role("button", name="Sign in")).to_be_visible()


def test_hatali_sifre_hata_mesaji_gosterir(page: Page):
    # Kayıtlı olmayan bir e-posta: test yöneticisinin hesap kilidi sayacı artmaz
    page.goto("/giris")
    giris_yap(page, "kayitsiz@chainguard.test", "yanlis-sifre-123")
    expect(page.get_by_text("Incorrect email or password.")).to_be_visible()
    expect(page).to_have_url(re.compile(r"/giris$"))


def test_gecersiz_eposta_form_dogrulamasina_takilir(page: Page):
    page.goto("/giris")
    giris_yap(page, "eposta-degil", "herhangi")
    expect(page.get_by_text("Enter a valid email address")).to_be_visible()


def test_giris_sonrasi_istenen_sayfaya_doner(page: Page, sunucu):
    page.goto("/olaylar")
    expect(page).to_have_url(re.compile(r"/giris"))
    giris_yap(page, sunucu.eposta, sunucu.sifre)
    expect(page).to_have_url(f"{sunucu.url}/olaylar")


def test_oturumu_kapatinca_giris_sayfasina_doner(oturum: Page, sunucu):
    oturum.get_by_role("button", name=re.compile("^User menu")).click()
    oturum.get_by_role("menuitem", name="Sign out").click()
    expect(oturum).to_have_url(re.compile(r"/giris$"))

    # Oturum gerçekten kapandı: korunan sayfa yine girişe yönlendirir
    oturum.goto("/tedarikciler")
    expect(oturum).to_have_url(re.compile(r"/giris\?yonlendir="))
