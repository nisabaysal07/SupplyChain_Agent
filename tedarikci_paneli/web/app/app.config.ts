export default defineAppConfig({
  ui: {
    colors: {
      primary: 'blue',
      // Sıcak gri: krem zeminle uyumlu (zemin ve yazı tonları app/assets/css/main.css'te)
      neutral: 'stone'
    },
    // Basınca hafif içe göçme: arayüz tıklamayı duyduğunu gösterir.
    // Açılır pencere ve modal animasyonları Nuxt UI'da zaten var(--ease-out) kullanır; eğri main.css'te güçlendirildi.
    button: {
      slots: {
        base: 'transition-[color,background-color,border-color,box-shadow,transform] duration-150 ease-out active:scale-[0.97] disabled:active:scale-100 aria-disabled:active:scale-100 motion-reduce:active:scale-100'
      }
    }
  }
})
