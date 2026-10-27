import type { Rol } from './kullanici'

// Oturum çerezinde yalnızca kimlik ve gösterim bilgisi tutulur; yetki her istekte kullanıcı kaydından okunur
declare module '#auth-utils' {
  interface User {
    id: string
    ad: string
    soyad: string
    eposta: string
    rol: Rol
  }
}

export {}
