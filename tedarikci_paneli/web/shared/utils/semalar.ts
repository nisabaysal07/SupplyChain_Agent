import { z } from 'zod'

// Formlar (tarayıcı) ve API'ler (sunucu) aynı doğrulama kurallarını kullanır.
// Dışa aktarım sonda topluca yapılır (bkz. shared/utils/etiketler.ts'deki mlly notu).

const SEVIYELER = ['dusuk', 'orta', 'yuksek'] as const

const eposta = z.string().trim().toLowerCase().email('Geçerli bir e-posta girin').max(254)

const yeniSifre = z.string()
  .min(12, 'Şifre en az 12 karakter olmalı')
  .max(128, 'Şifre en fazla 128 karakter olabilir')

const GirisSemasi = z.object({
  eposta,
  sifre: z.string().min(1, 'Şifrenizi girin').max(128)
})

const ProfilSemasi = z.object({
  ad: z.string().trim().min(1, 'Ad boş olamaz').max(60),
  soyad: z.string().trim().max(60)
})

const SifreSemasi = z.object({
  mevcut: z.string().min(1, 'Mevcut şifrenizi girin').max(128),
  yeni: yeniSifre,
  tekrar: z.string()
}).refine(v => v.yeni === v.tekrar, { message: 'Şifreler aynı değil', path: ['tekrar'] })
  .refine(v => v.yeni !== v.mevcut, { message: 'Yeni şifre eskisiyle aynı olamaz', path: ['yeni'] })

const BildirimSemasi = z.object({
  eposta: z.boolean(),
  uygulamaIci: z.boolean(),
  seviyeler: z.array(z.enum(SEVIYELER)).max(3)
})

const SistemSemasi = z.object({
  senkronizasyonSaat: z.union([z.literal(6), z.literal(12), z.literal(24)])
})

// Giriş sonrası yönlendirme yalnızca site içi bir yola yapılır ("//kotu.site" veya "https://..." reddedilir)
function guvenliYonlendirme(hedef: unknown): string {
  return typeof hedef === 'string' && /^\/(?![/\\])/.test(hedef) ? hedef : '/'
}

export { BildirimSemasi, GirisSemasi, guvenliYonlendirme, ProfilSemasi, SifreSemasi, SistemSemasi, yeniSifre }
