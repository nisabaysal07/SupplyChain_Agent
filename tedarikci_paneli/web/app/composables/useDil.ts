import en from '~/i18n/en'
import tr from '~/i18n/tr'

// Arayüz dili: varsayılan İngilizce, seçim "dil" çerezinde bir yıl tutulur (sunucu da aynı dilde çizer).
// t('pano.riskHaritasi'), t('genel.gun', { n: 3 }) → "3 days"; bulunamayan anahtar İngilizceden, o da yoksa anahtarın kendisi.
// Para / sayı / tarih biçimleri de seçili dile göredir: const { para, tarih } = useDil()

const SOZLUKLER = { en, tr }
type Parametreler = Record<string, string | number>

function bul(sozluk: unknown, anahtar: string): unknown {
  return anahtar.split('.').reduce<unknown>((o, k) => (o as Record<string, unknown> | undefined)?.[k], sozluk)
}

export function useDil() {
  const cerez = useCookie<string | null>('dil', { maxAge: 60 * 60 * 24 * 365, sameSite: 'lax', path: '/' })
  const dil = useState<Dil>('dil', () => (cerez.value === 'tr' ? 'tr' : 'en'))

  function dilSec(yeni: Dil) {
    dil.value = yeni
    cerez.value = yeni
  }

  function t(anahtar: string, p?: Parametreler): string {
    let deger = bul(SOZLUKLER[dil.value], anahtar) ?? bul(en, anahtar)
    // [tekil, çoğul] çiftinde n'ye göre seçilir
    if (Array.isArray(deger)) deger = deger[p?.n === 1 ? 0 : 1]
    if (typeof deger !== 'string') return anahtar
    return p ? deger.replace(/\{(\w+)\}/g, (tamami, k: string) => (k in p ? String(p[k]) : tamami)) : deger
  }

  // Sözlükte olmayan ad (veritabanından gelen yeni ülke / yer) olduğu gibi gösterilir
  const ulkeAdi = (ad: string) => (SOZLUKLER[dil.value].ulke as Record<string, string>)[ad] ?? ad
  const yerAdi = (ad: string) => (SOZLUKLER[dil.value].yer as Record<string, string>)[ad] ?? ad

  const b = () => bicimler(dil.value)
  return {
    dil: readonly(dil),
    dilSec,
    t,
    ulkeAdi,
    yerAdi,
    para: (v: number) => b().para(v),
    fiyat: (v: number) => b().fiyat(v),
    sayi: (v: number) => b().sayi(v),
    ondalik: (v: number) => b().ondalik(v),
    yuzde: (oran: number) => b().yuzde(oran),
    tarih: (iso: string) => b().tarih(iso),
    tarihSaat: (iso: string) => b().tarihSaat(iso),
    saat: (d: Date) => b().saat(d),
    goreli: (deger: number, birim: Intl.RelativeTimeFormatUnit) => b().goreli(deger, birim)
  }
}
