
export default defineNuxtConfig({
  compatibilityDate: '2026-10-01',
  modules: ['@nuxt/ui', 'nuxt-security', 'nuxt-auth-utils'],
  css: ['~/assets/css/main.css'],
  // Yalnızca açık (krem) tema; işletim sistemi karanlık modda olsa da değişmez
  ui: { colorMode: false },
  devtools: { enabled: false },

  app: {
    head: {
      // Varsayılan dil İngilizce; kullanıcı Türkçeye geçerse app.vue günceller
      htmlAttrs: { lang: 'en' },
      title: 'ChainGuard AI'
    }
  },

  // Gizli değerler yalnızca sunucuda kalır; `public` altına hiçbir anahtar konmaz.
  // Üretimde ortam değişkeniyle verilir: NUXT_TAVILY_API_KEY, NUXT_NEMOTRON_API_KEY,
  // NUXT_SESSION_PASSWORD, NUXT_ILK_YONETICI_EPOSTA, NUXT_ILK_YONETICI_SIFRE, NUXT_MODEL_API_TOKEN.
  // PostgreSQL bağlantısı runtimeConfig'de değil: proje kökündeki .env'nin POSTGRES_* değerleri kullanılır (server/utils/veritabani.ts)
  runtimeConfig: {
    tavilyApiKey: '',
    nemotronApiKey: '',
    // Modelin rapor gönderirken kullandığı erişim anahtarı (en az 32 karakter); boşsa model ucu kapalıdır
    modelApiToken: '',
    // Hiç kullanıcı yokken ilk yönetici bu bilgilerle oluşturulur (server/plugins/ilkYonetici.ts)
    ilkYonetici: { eposta: '', sifre: '' },
    // Hız sınırı için istemci adresini taşıyan başlık (NUXT_GUVENILIR_IP_BASLIGI, ör. x-forwarded-for).
    // Boşsa yalnızca bağlantının adresi kullanılır; yalnızca başlığı kendisi yazan bir proxy arkasında tanımlayın.
    guvenilirIpBasligi: '',
    // Oturum çerezi şifreli ve httpOnly'dir; 8 saat sonra yeniden giriş gerekir.
    // Şifreleme anahtarı (password) buraya yazılmaz: nuxt-auth-utils onu NUXT_SESSION_PASSWORD'den okur.
    session: { maxAge: 60 * 60 * 8 } as { maxAge: number, password: string }
  },

  // Kullanıcılar ve ayarlar sunucuda .data/ klasöründe tutulur (git'e girmez).
  // E2E testleri CHAINGUARD_VERI_DIZINI ile geçici bir klasör verir; asıl veriye dokunulmaz.
  nitro: {
    storage: {
      veri: { driver: 'fs', base: process.env.CHAINGUARD_VERI_DIZINI || './.data/veri' }
    }
  },

  // İkonlar sunucu paketinden verilir; tarayıcı dışarıdaki Iconify API'sine istek atmaz
  icon: {
    serverBundle: { collections: ['lucide'] }
  },

  security: {
    headers: {
      contentSecurityPolicy: {
        'img-src': ['\'self\'', 'data:'],
        'connect-src': ['\'self\'']
      }
    },
    rateLimiter: {
      tokensPerInterval: 150,
      interval: 300000
    },
    requestSizeLimiter: {
      maxRequestSizeInBytes: 2_000_000,
      maxUploadFileRequestInBytes: 5_000_000
    }
  },

  // Şifre denemelerine sıkı sınır: dakikada 5 deneme (geliştirmede de açık)
  routeRules: {
    // Raporlar ayrı bir sayfa değil: modelin çıkarımı her olayın detayında gösterilir
    '/raporlar': { redirect: '/olaylar' },
    '/api/auth/giris': {
      security: { rateLimiter: { tokensPerInterval: 5, interval: 60000 } }
    },
    // Excel dosyası ikili veridir; XSS süzgeci multipart gövdeyi metin sanıp reddetmesin
    '/api/yukleme': {
      security: { xssValidator: false }
    },
    // Model raporları "<%5" gibi karakterler içerebilir; genel XSS süzgeci yerine zod şeması doğrular
    // ve arayüz her şeyi düz metin olarak gösterir. Rapor gövdesi en fazla 1 MB.
    '/api/model/**': {
      security: {
        xssValidator: false,
        requestSizeLimiter: { maxRequestSizeInBytes: 1_000_000, maxUploadFileRequestInBytes: 1_000_000 }
      }
    }
  },

  // Geliştirmede HMR istekleri hız sınırına ve COEP'e takılmasın
  $development: {
    security: {
      rateLimiter: false,
      headers: { crossOriginEmbedderPolicy: 'unsafe-none' }
    }
  }
})
