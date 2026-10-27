// Grafiklerde imleç (veya klavye odağı) üzerindeki işaretin ipucunu gösterir.
// Konum, grafiği saran "relative" kapsayıcıya göredir.
export interface IpucuSatiri {
  ad: string
  deger: string
  renk?: string
}

export function useIpucu() {
  const kapsayici = ref<HTMLElement | null>(null)
  const ipucu = reactive({ gorunur: false, x: 0, y: 0, baslik: '', satirlar: [] as IpucuSatiri[] })

  function konumla(olay: MouseEvent | FocusEvent) {
    const kutu = kapsayici.value?.getBoundingClientRect()
    if (!kutu) return
    if (olay instanceof MouseEvent) {
      ipucu.x = olay.clientX - kutu.left
      ipucu.y = olay.clientY - kutu.top
    }
    else {
      const hedef = (olay.target as Element).getBoundingClientRect()
      ipucu.x = hedef.left + hedef.width / 2 - kutu.left
      ipucu.y = hedef.top - kutu.top
    }
  }

  function goster(olay: MouseEvent | FocusEvent, baslik: string, satirlar: IpucuSatiri[]) {
    konumla(olay)
    Object.assign(ipucu, { gorunur: true, baslik, satirlar })
  }

  function gizle() {
    ipucu.gorunur = false
  }

  return { kapsayici, ipucu, goster, konumla, gizle }
}
