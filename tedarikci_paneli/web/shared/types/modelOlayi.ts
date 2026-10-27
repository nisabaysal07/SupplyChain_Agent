import type { z } from 'zod'
import type { CikarimSemasi } from '../utils/modelOlayi'
import type { Olay } from './veri'

// Modelin bir haber için yaptığı çıkarım (doğrulanmış hâli)
export type ModelCikarimi = z.output<typeof CikarimSemasi>

// Depoda tutulan olay: modelin gönderdiği haber + çıkarımı + sunucunun eklediği alınma zamanı
export type KayitliOlay = Olay & { cikarim?: ModelCikarimi, alinma: string }
