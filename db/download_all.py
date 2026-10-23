"""
Tüm YAML dosyalarını (db/yaml/) doğru sırayla veritabanına kaydeder.

Çalıştırma:  python db/download_all.py   (proje klasöründen)
         ya da  python download_all.py   (db klasöründen)

Sıra önemlidir, çünkü tablolar birbirine bağlıdır:
    countries → rate_sources → locations → items → tariffs

Hepsi tek transaction içinde çalışır: herhangi bir adımda hata olursa
hiçbir tabloya değişiklik kaydedilmez. Tekrar çalıştırmak güvenlidir.
"""
import country_download
import items_download
import location_download
import rate_source_download
import tariffs_download
from yaml_db import main

STEPS = [
    country_download.load,      # countries
    rate_source_download.load,  # rate_sources
    location_download.load,     # locations     (countries'e bağlı)
    items_download.load,        # items         (rate_sources'a bağlı)
    tariffs_download.load,      # tariffs       (items, countries, rate_sources'a bağlı)
]

if __name__ == "__main__":
    main(*STEPS)
    print("Tüm tablolar başarıyla kaydedildi.")
