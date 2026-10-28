import type { Dil } from '../types/dil'

// Para, sayı ve tarih biçimleri arayüz diline göre (en: $1,234 · 12 Oct 2026, tr: 1.234 $ · 12 Eki 2026).
// Biçimleyiciler dil başına bir kez oluşturulur; arayüz bunları useDil() üzerinden kullanır.

const YEREL: Record<Dil, string> = { en: 'en-US', tr: 'tr-TR' }

function olustur(dil: Dil) {
  const yerel = YEREL[dil]
  const para = new Intl.NumberFormat(yerel, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
  const kesirliPara = new Intl.NumberFormat(yerel, { style: 'currency', currency: 'USD', minimumFractionDigits: 2 })
  const sayi = new Intl.NumberFormat(yerel)
  const ondalik = new Intl.NumberFormat(yerel, { maximumFractionDigits: 1 })
  const yuzde = new Intl.NumberFormat(yerel, { style: 'percent', maximumFractionDigits: 1 })
  const tarih = new Intl.DateTimeFormat(yerel, { day: 'numeric', month: 'short', year: 'numeric' })
  const tarihSaat = new Intl.DateTimeFormat(yerel, {
    day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Istanbul'
  })
  const saat = new Intl.DateTimeFormat(yerel, { hour: '2-digit', minute: '2-digit' })
  const goreli = new Intl.RelativeTimeFormat(dil, { numeric: 'auto' })
  return {
    yerel,
    para: (v: number) => para.format(v),
    fiyat: (v: number) => kesirliPara.format(v),
    sayi: (v: number) => sayi.format(v),
    ondalik: (v: number) => ondalik.format(v),
    // 0,042 → "4.2%" / "%4,2"
    yuzde: (oran: number) => yuzde.format(oran),
    tarih: (iso: string) => tarih.format(new Date(`${iso}T00:00:00`)),
    tarihSaat: (iso: string) => tarihSaat.format(new Date(iso)),
    saat: (d: Date) => saat.format(d),
    goreli: (deger: number, birim: Intl.RelativeTimeFormatUnit) => goreli.format(deger, birim)
  }
}

const BICIMLER = { en: olustur('en'), tr: olustur('tr') }

export function bicimler(dil: Dil) {
  return BICIMLER[dil]
}
