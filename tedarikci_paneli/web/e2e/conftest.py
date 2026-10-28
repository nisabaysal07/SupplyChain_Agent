"""E2E testleri için ortak hazırlık.

Testler kendi Nuxt geliştirme sunucusunu ayrı bir portta başlatır:
- Veri (kullanıcılar, olaylar, bildirimler) geçici bir klasöre yazılır (CHAINGUARD_VERI_DIZINI);
  .data/veri'deki asıl veriye dokunulmaz.
- İlk yönetici, oturum anahtarı ve model erişim anahtarı her çalıştırmada rastgele üretilir.
- Proje kökündeki .env'den yalnızca POSTGRES_* değerleri alınır. Sunucu veritabanından yalnızca okur
  (olaylar geçici klasöre yazılır); veritabanı kapalıysa olay testleri atlanır.

Çalıştırma (web/ klasöründe):  python -m pytest e2e
Çalışan bir sunucuya karşı:    CHAINGUARD_E2E_URL=http://localhost:3001 ... (aynı değişkenlerle başlatılmış olmalı)
"""

import json
import os
import secrets
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

WEB_DIZINI = Path(__file__).resolve().parent.parent
KOK_ENV = WEB_DIZINI.parent.parent / ".env"
ORNEK_OLAYLAR = WEB_DIZINI / "ornek" / "olaylar"

# İlk derleme yavaş olabilir (Nuxt dev ilk istekte sayfayı derler)
SUNUCU_BEKLEME_SN = 240
expect.set_options(timeout=20_000)


def _bos_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _postgres_ayarlari() -> dict[str, str]:
    """Kök .env'deki POSTGRES_* satırları (ortamda zaten tanımlı olanlar önceliklidir)."""
    ayarlar = {}
    if KOK_ENV.exists():
        for satir in KOK_ENV.read_text(encoding="utf-8").splitlines():
            anahtar, ayrac, deger = satir.strip().partition("=")
            if ayrac and anahtar.startswith("POSTGRES_"):
                ayarlar[anahtar] = deger.strip().strip("\"'")
    return {k: os.environ.get(k, v) for k, v in ayarlar.items()}


def _hazir_mi(url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{url}/giris", timeout=60) as yanit:
            return yanit.status == 200
    except (urllib.error.URLError, OSError):
        return False


def _sureci_durdur(surec: subprocess.Popen) -> None:
    if surec.poll() is not None:
        return
    if os.name == "nt":
        # npx → node alt süreçleri de kapansın
        subprocess.run(["taskkill", "/PID", str(surec.pid), "/T", "/F"], capture_output=True)
    else:
        surec.terminate()
    surec.wait(timeout=30)


class Sunucu:
    def __init__(self, url: str, eposta: str, sifre: str, model_anahtari: str):
        self.url = url
        self.eposta = eposta
        self.sifre = sifre
        self.model_anahtari = model_anahtari

    def olay_gonder(self, olay: dict) -> dict:
        """Modelin yaptığı gibi /api/model/olaylar ucuna bir olay gönderir."""
        istek = urllib.request.Request(
            f"{self.url}/api/model/olaylar",
            data=json.dumps(olay).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.model_anahtari}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(istek, timeout=60) as yanit:
            return json.loads(yanit.read() or b"{}")


@pytest.fixture(scope="session")
def sunucu():
    eposta = "e2e-yonetici@chainguard.test"
    sifre = secrets.token_urlsafe(18)
    model_anahtari = secrets.token_urlsafe(32)

    hazir_url = os.environ.get("CHAINGUARD_E2E_URL")
    if hazir_url:
        yield Sunucu(
            hazir_url.rstrip("/"),
            os.environ["CHAINGUARD_E2E_EPOSTA"],
            os.environ["CHAINGUARD_E2E_SIFRE"],
            os.environ.get("CHAINGUARD_E2E_MODEL_ANAHTARI", ""),
        )
        return

    veri_dizini = tempfile.mkdtemp(prefix="chainguard-e2e-")
    port = _bos_port()
    url = f"http://127.0.0.1:{port}"
    ortam = {
        **os.environ,
        "CHAINGUARD_VERI_DIZINI": veri_dizini,
        "NUXT_ILK_YONETICI_EPOSTA": eposta,
        "NUXT_ILK_YONETICI_SIFRE": sifre,
        "NUXT_SESSION_PASSWORD": secrets.token_urlsafe(48),
        "NUXT_MODEL_API_TOKEN": model_anahtari,
        **_postgres_ayarlari(),
        # Dış servisler kapalı
        "NUXT_TAVILY_API_KEY": "",
        "NUXT_NEMOTRON_API_KEY": "",
        # Açık bir `npm run dev` varken de ikinci sunucu başlayabilsin
        "NUXT_IGNORE_LOCK": "1",
    }
    npx = shutil.which("npx") or "npx"
    gunluk = open(Path(veri_dizini) / "sunucu.log", "w", encoding="utf-8", errors="replace")
    surec = subprocess.Popen(
        [npx, "nuxt", "dev", "--port", str(port), "--host", "127.0.0.1"],
        cwd=WEB_DIZINI,
        env=ortam,
        stdout=gunluk,
        stderr=subprocess.STDOUT,
    )
    try:
        bitis = time.monotonic() + SUNUCU_BEKLEME_SN
        while not _hazir_mi(url):
            if surec.poll() is not None or time.monotonic() > bitis:
                gunluk.flush()
                kayit = (Path(veri_dizini) / "sunucu.log").read_text(encoding="utf-8", errors="replace")
                pytest.exit(f"Test sunucusu açılamadı ({url}). Sunucu çıktısı:\n{kayit[-4000:]}", returncode=1)
            time.sleep(1)
        yield Sunucu(url, eposta, sifre, model_anahtari)
    finally:
        _sureci_durdur(surec)
        gunluk.close()
        shutil.rmtree(veri_dizini, ignore_errors=True)


@pytest.fixture(scope="session")
def base_url(sunucu):
    # pytest-playwright, page.goto("/...") çağrılarını bu adrese göre çözer
    return sunucu.url


@pytest.fixture(scope="session")
def ornek_olaylar(sunucu) -> list[dict]:
    """ornek/olaylar/*.json dosyalarını sunucuya gönderir ve gönderilenleri döndürür."""
    olaylar = [json.loads(d.read_text(encoding="utf-8")) for d in sorted(ORNEK_OLAYLAR.glob("*.json"))]
    for olay in olaylar:
        try:
            sunucu.olay_gonder(olay)
        except urllib.error.HTTPError as hata:
            if hata.code == 503:
                pytest.skip(f"Olay testleri PostgreSQL ister (supply_db): {hata.reason}")
            raise
    return olaylar


def hidrasyonu_bekle(page: Page) -> None:
    """Vue sunucudan gelen HTML'i devralana kadar bekler; öncesinde yazılan değerler v-model'e geçmez."""
    page.wait_for_function("() => !!document.getElementById('__nuxt')?.__vue_app__")


def giris_yap(page: Page, eposta: str, sifre: str) -> None:
    # Arayüz varsayılan olarak İngilizce açılır (dil çerezi yokken)
    hidrasyonu_bekle(page)
    page.get_by_label("Email").fill(eposta)
    page.get_by_label("Password").fill(sifre)
    page.get_by_role("button", name="Sign in").click()


@pytest.fixture(scope="session")
def oturum_durumu(browser, sunucu, tmp_path_factory) -> Path:
    """Bir kez giriş yapıp çerezi saklar: giriş ucu dakikada 5 denemeyle sınırlı (nuxt.config.ts)."""
    dosya = tmp_path_factory.mktemp("oturum") / "durum.json"
    baglam = browser.new_context(base_url=sunucu.url)
    sayfa = baglam.new_page()
    sayfa.goto("/giris")
    giris_yap(sayfa, sunucu.eposta, sunucu.sifre)
    expect(sayfa).not_to_have_url(f"{sunucu.url}/giris")
    baglam.storage_state(path=dosya)
    baglam.close()
    return dosya


@pytest.fixture
def oturum(browser, browser_context_args, oturum_durumu) -> Page:
    """Yönetici olarak giriş yapılmış sayfa."""
    baglam = browser.new_context(**browser_context_args, storage_state=oturum_durumu)
    sayfa = baglam.new_page()
    sayfa.goto("/")
    hidrasyonu_bekle(sayfa)
    yield sayfa
    baglam.close()
