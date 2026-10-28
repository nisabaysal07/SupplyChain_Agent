import { z } from 'zod'

// Formlar (tarayıcı) ve API'ler (sunucu) aynı doğrulama kurallarını kullanır.
// Hata mesajları sözlük anahtarıdır (app/i18n → dogrulama); formlar UFormField'ın #error yuvasında t() ile çevirir.
// Dışa aktarım sonda topluca yapılır (bkz. shared/utils/etiketler.ts'deki mlly notu).

const SEVIYELER = ['dusuk', 'orta', 'yuksek'] as const

const eposta = z.string().trim().toLowerCase().email('dogrulama.eposta').max(254)

const yeniSifre = z.string()
  .min(12, 'dogrulama.sifreMin')
  .max(128, 'dogrulama.sifreMax')

const GirisSemasi = z.object({
  eposta,
  sifre: z.string().min(1, 'dogrulama.sifreGir').max(128)
})

const ProfilSemasi = z.object({
  ad: z.string().trim().min(1, 'dogrulama.adBos').max(60),
  soyad: z.string().trim().max(60)
})

const SifreSemasi = z.object({
  mevcut: z.string().min(1, 'dogrulama.mevcutGir').max(128),
  yeni: yeniSifre,
  tekrar: z.string()
}).refine(v => v.yeni === v.tekrar, { message: 'dogrulama.ayniDegil', path: ['tekrar'] })
  .refine(v => v.yeni !== v.mevcut, { message: 'dogrulama.eskisiyleAyni', path: ['yeni'] })

const BildirimSemasi = z.object({
  eposta: z.boolean(),
  uygulamaIci: z.boolean(),
  seviyeler: z.array(z.enum(SEVIYELER)).max(3)
})

const SistemSemasi = z.object({
  senkronizasyonSaat: z.union([z.literal(1), z.literal(3), z.literal(6), z.literal(12), z.literal(24)])
})

// Giriş sonrası yönlendirme yalnızca site içi bir yola yapılır ("//kotu.site" veya "https://..." reddedilir)
function guvenliYonlendirme(hedef: unknown): string {
  return typeof hedef === 'string' && /^\/(?![/\\])/.test(hedef) ? hedef : '/'
}

export { BildirimSemasi, GirisSemasi, guvenliYonlendirme, ProfilSemasi, SifreSemasi, SistemSemasi, yeniSifre }
