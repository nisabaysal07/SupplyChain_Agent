// Giriş yapmamış kullanıcı yalnızca giriş sayfasını görebilir.
// Asıl koruma sunucudadır (server/middleware/oturum.ts); bu yönlendirme kullanıcı deneyimi içindir.
export default defineNuxtRouteMiddleware((to) => {
  const { loggedIn } = useUserSession()
  if (to.path === '/giris') {
    if (loggedIn.value) return navigateTo(guvenliYonlendirme(to.query.yonlendir))
    return
  }
  if (!loggedIn.value) {
    return navigateTo({ path: '/giris', query: to.fullPath === '/' ? {} : { yonlendir: to.fullPath } })
  }
})
