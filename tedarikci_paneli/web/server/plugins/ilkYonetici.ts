// Hiç kullanıcı yoksa ilk yöneticiyi ortam değişkenlerinden oluşturur:
//   NUXT_ILK_YONETICI_EPOSTA, NUXT_ILK_YONETICI_SIFRE
// Kullanıcı varsa hiçbir şey yapmaz; ilk girişten sonra şifreyi değiştirip bu değişkenleri silin.
export default defineNitroPlugin(async () => {
  const { ilkYonetici } = useRuntimeConfig()
  if ((await kullanicilariListele()).length) return

  if (!ilkYonetici.eposta || !ilkYonetici.sifre) {
    console.warn('[ChainGuard] Kayıtlı kullanıcı yok. NUXT_ILK_YONETICI_EPOSTA ve NUXT_ILK_YONETICI_SIFRE ile ilk yöneticiyi tanımlayın.')
    return
  }
  const sonuc = yeniSifre.safeParse(ilkYonetici.sifre)
  if (!sonuc.success) {
    console.error('[ChainGuard] NUXT_ILK_YONETICI_SIFRE geçersiz:', sonuc.error.issues[0]?.message)
    return
  }
  await kullaniciOlustur({ ad: 'Yönetici', soyad: '', eposta: ilkYonetici.eposta, rol: 'yonetici', sifre: ilkYonetici.sifre })
  console.info(`[ChainGuard] İlk yönetici oluşturuldu: ${ilkYonetici.eposta}`)
})
