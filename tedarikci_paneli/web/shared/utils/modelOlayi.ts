import { z } from 'zod'
import type { OlayKapsami } from '../types/veri'

// Arkadaşının modelinin gönderdiği haber (olay) ve o haberden yaptığı çıkarım. Açıklaması: web/MODEL_ENTEGRASYONU.md
// Olay, risk skoruna ve haritaya girer; çıkarım Olaylar sayfasında olayın detayında gösterilir.
// Bütün metinler düz metin olarak gösterilir (HTML işlenmez); bağlantılar yalnızca https olabilir.
// Dışa aktarım sonda topluca yapılır (bkz. shared/utils/etiketler.ts'deki mlly notu).

const KIMLIK = /^[A-Za-z0-9_-]{1,100}$/
const seviye = z.enum(['dusuk', 'orta', 'yuksek'])
const metin = (enFazla: number) => z.string().trim().min(1).max(enFazla)
const httpsUrl = z.string().max(2000).refine(u => /^https:\/\/[^\s]+$/.test(u), 'Bağlantı https:// ile başlamalı')
const liste = (oge: z.ZodString) => z.array(oge).max(100).default([])

const CikarimSemasi = z.object({
  baslik: metin(200),
  olusturma: z.iso.datetime({ offset: true }),
  model: z.object({ ad: metin(100), surum: metin(50) }),
  ozet: metin(5000),
  genelDegerlendirme: z.object({
    seviye,
    skor: z.number().min(0).max(100).optional(),
    guven: z.number().min(0).max(1).optional()
  }),
  bulgular: z.array(z.object({
    baslik: metin(200),
    aciklama: metin(3000),
    seviye,
    tedarikciIdleri: z.array(z.number().int().positive()).max(100).default([])
  })).max(50).default([]),
  oneriler: z.array(z.object({ metin: metin(1000), oncelik: seviye })).max(50).default([]),
  kaynaklar: z.array(z.object({ ad: metin(200), url: httpsUrl })).max(50).default([])
})

const ModelOlaySemasi = z.object({
  id: z.string().regex(KIMLIK, 'id yalnızca harf, rakam, - ve _ içerebilir (en fazla 100)'),
  baslik: metin(200),
  ozet: metin(2000),
  tur: z.enum(['vergi', 'grev', 'liman', 'dogal_afet', 'jeopolitik', 'fiyat']),
  siddet: seviye,
  tarih: z.iso.date(),
  bitisTarihi: z.iso.date().nullable().default(null),
  kaynak: z.object({ ad: metin(200), url: httpsUrl.nullable().default(null) }),
  kapsam: z.object({
    ulkeler: liste(metin(100)),
    noktalar: liste(metin(200)),
    hs6: liste(z.string().regex(/^[0-9]{6}$/, 'hs6 altı haneli olmalı')),
    firmalar: liste(metin(100))
  }).refine(k => k.ulkeler.length + k.noktalar.length + k.hs6.length + k.firmalar.length > 0,
    'kapsam en az bir ölçüt içermeli (ulkeler, noktalar, hs6 veya firmalar)'),
  ekMaliyetOrani: z.number().min(0).max(5).optional(),
  gecikmeVar: z.boolean().default(false),
  ornek: z.boolean().default(false),
  cikarim: CikarimSemasi.optional()
}).refine(o => !o.bitisTarihi || o.bitisTarihi >= o.tarih, { message: 'bitisTarihi, tarih\'ten önce olamaz', path: ['bitisTarihi'] })

// Panelin bildiği adlar: kapsamdaki değerler bunlarla birebir eşleşmeli
interface Referans {
  ulkeler: string[]
  noktalar: string[]
  hs6: string[]
  firmalar: string[]
}

// Hiçbir tedarikçiyle eşleşmeyen kapsam değerleri (yazım hatası olabilir); olay yine kaydedilir
function kapsamUyarilari(kapsam: OlayKapsami, referans: Referans): string[] {
  const alanlar = ['ulkeler', 'noktalar', 'hs6', 'firmalar'] as const
  return alanlar.flatMap(alan => (kapsam[alan] ?? [])
    .filter(deger => !referans[alan].includes(deger))
    .map(deger => `kapsam.${alan}: "${deger}" panelde tanımlı değil`))
}

export { CikarimSemasi, KIMLIK, kapsamUyarilari, ModelOlaySemasi }
export type { Referans }
