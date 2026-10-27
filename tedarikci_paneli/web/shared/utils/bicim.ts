const para = new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
const kesirliPara = new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 })
const sayi = new Intl.NumberFormat('tr-TR')
const tarih = new Intl.DateTimeFormat('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' })
const tarihSaat = new Intl.DateTimeFormat('tr-TR', {
  day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Istanbul'
})

export const paraBicimi = (v: number) => para.format(v)
export const fiyatBicimi = (v: number) => kesirliPara.format(v)
export const sayiBicimi = (v: number) => sayi.format(v)
export const tarihBicimi = (iso: string) => tarih.format(new Date(`${iso}T00:00:00`))
export const tarihSaatBicimi = (iso: string) => tarihSaat.format(new Date(iso))
