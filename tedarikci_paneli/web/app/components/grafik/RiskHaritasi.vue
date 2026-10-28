<script setup lang="ts">
import { geoInterpolate, geoNaturalEarth1, geoPath } from 'd3-geo'
import type { Feature, FeatureCollection, Geometry } from 'geojson'
import { feature } from 'topojson-client'
import type { GeometryCollection, Topology } from 'topojson-specification'
import dunya from 'world-atlas/countries-110m.json'

// Tedarikçilerin çıkış noktaları (daire: büyüklük = yıllık alım, renk = en yüksek risk) ve Türkiye'ye rotaları.
// Harita verisi pakete gömülüdür; tarayıcı dışarıdan harita indirmez. Noktaların konumu veritabanından gelir (/api/konumlar).
const props = defineProps<{ tedarikciler: RiskliTedarikci[], konumlar: Record<string, HaritaKonumu> }>()
const { t, para, ulkeAdi, yerAdi } = useDil()

const G = 800
const Y = 420
const SIRA: Record<Seviye, number> = { dusuk: 0, orta: 1, yuksek: 2 }

const ulkeler = (feature(dunya as unknown as Topology, (dunya as unknown as Topology).objects.countries as GeometryCollection) as FeatureCollection).features

interface Grup {
  bolge: string
  konum: HaritaKonumu
  tedarikciler: RiskliTedarikci[]
  alim: number
  seviye: Seviye
}

const gruplar = computed<Grup[]>(() => {
  const harita = new Map<string, Grup>()
  for (const t of props.tedarikciler) {
    const k = props.konumlar[t.rota.cikis]
    if (!k) continue
    const g = harita.get(k.bolge) ?? { bolge: k.bolge, konum: k, tedarikciler: [], alim: 0, seviye: 'dusuk' as Seviye }
    g.tedarikciler.push(t)
    g.alim += t.yillikAlimUsd
    if (SIRA[t.risk.seviye] > SIRA[g.seviye]) g.seviye = t.risk.seviye
    harita.set(k.bolge, g)
  }
  return [...harita.values()]
})

const bilinmeyenler = computed(() => props.tedarikciler.filter(t => !props.konumlar[t.rota.cikis]))

const varislar = computed(() => [...new Set(props.tedarikciler.map(t => t.rota.varis))]
  .map(ad => props.konumlar[ad])
  .filter((k): k is HaritaKonumu => Boolean(k)))

// Görünür alan: bütün noktaları biraz pay bırakarak kapsar
const projeksiyon = computed(() => {
  const noktalar = [...gruplar.value.map(g => g.konum), ...varislar.value]
  const boylamlar = noktalar.map(n => n.boylam)
  const enlemler = noktalar.map(n => n.enlem)
  const kutu: Feature<Geometry> = {
    type: 'Feature',
    properties: {},
    geometry: {
      type: 'MultiPoint',
      coordinates: noktalar.length
        // Sağda daha geniş pay: doğudaki noktaların etiketleri sağa yazılır
        ? [[Math.min(...boylamlar) - 8, Math.min(...enlemler) - 6], [Math.max(...boylamlar) + 18, Math.max(...enlemler) + 4]]
        : [[20, 0], [140, 50]]
    }
  }
  return geoNaturalEarth1().fitExtent([[16, 16], [G - 16, Y - 16]], kutu)
})

const yol = computed(() => geoPath(projeksiyon.value))
const xy = (k: HaritaKonumu) => projeksiyon.value([k.boylam, k.enlem]) ?? [0, 0]

const vurguluUlkeler = computed(() => new Set(
  [...props.tedarikciler.map(x => x.menseUlke), 'Türkiye'].map(u => ULKE_KODLARI[u]).filter(Boolean)
))

const ulkeYollari = computed(() => ulkeler.map(u => ({
  id: String(u.id),
  d: yol.value(u) ?? '',
  vurgulu: vurguluUlkeler.value.has(String(u.id))
})))

const enBuyukAlim = computed(() => Math.max(1, ...gruplar.value.map(g => g.alim)))
const yaricap = (alim: number) => 7 + 15 * Math.sqrt(alim / enBuyukAlim.value)

// Büyük daireler altta kalsın ki küçükler görünsün
const daireler = computed(() => [...gruplar.value]
  .sort((a, b) => b.alim - a.alim)
  .map(g => ({ ...g, xy: xy(g.konum), r: yaricap(g.alim) })))

const aktifBolge = ref<string | null>(null)

// Rotalar büyük daire yayı olarak çizilir (gerçek deniz yolu değildir)
const rotalar = computed(() => props.tedarikciler.flatMap((t) => {
  const a = props.konumlar[t.rota.cikis]
  const b = props.konumlar[t.rota.varis]
  if (!a || !b) return []
  const ara = geoInterpolate([a.boylam, a.enlem], [b.boylam, b.enlem])
  const d = yol.value({ type: 'LineString', coordinates: Array.from({ length: 33 }, (_, i) => ara(i / 32)) }) ?? ''
  return [{ id: t.id, d, hava: t.rota.mod === 'hava', bolge: a.bolge }]
}))

function etiketKonumu(k: HaritaKonumu, r: number, [x, y]: [number, number]) {
  const pay = r + 5
  switch (ETIKET_YONLERI[k.bolge] ?? 'sag') {
    case 'sol': return { x: x - pay, y: y + 4, anchor: 'end' }
    case 'ust': return { x, y: y - pay, anchor: 'middle' }
    case 'alt': return { x, y: y + pay + 9, anchor: 'middle' }
    default: return { x: x + pay, y: y + 4, anchor: 'start' }
  }
}

const { kapsayici, ipucu, goster, konumla, gizle } = useIpucu()

function grupIpucu(olay: MouseEvent | FocusEvent, g: Grup) {
  aktifBolge.value = g.bolge
  goster(olay, `${yerAdi(g.bolge)} · ${[...new Set(g.tedarikciler.map(x => ulkeAdi(x.menseUlke)))].join(', ')}`, [
    ...g.tedarikciler.map(x => ({
      ad: `${x.firma} · ${x.parca}`,
      deger: `${x.risk.skor} · ${t(`seviye.${x.risk.seviye}`)}`,
      renk: SEVIYE_VIZ_RENGI[x.risk.seviye]
    })),
    { ad: t('alan.yillikAlim'), deger: para(g.alim) }
  ])
}

function birak() {
  aktifBolge.value = null
  gizle()
}

const sayilar = computed(() => (['yuksek', 'orta', 'dusuk'] as const).map(s => ({
  seviye: s,
  sayi: props.tedarikciler.filter(t => t.risk.seviye === s).length
})))

const SEVIYE_IKONU: Record<Seviye, string> = {
  dusuk: 'i-lucide-circle-check', orta: 'i-lucide-circle-alert', yuksek: 'i-lucide-triangle-alert'
}
</script>

<template>
  <div ref="kapsayici" class="relative">
    <svg
      :viewBox="`0 0 ${G} ${Y}`"
      class="w-full h-auto rounded-md bg-muted"
      role="img"
      :aria-label="t('grafik.haritaAria')"
    >
      <g aria-hidden="true">
        <path
          v-for="u in ulkeYollari"
          :key="u.id"
          :d="u.d"
          :fill="u.vurgulu ? 'var(--viz-kara-vurgu)' : 'var(--viz-kara)'"
          stroke="var(--ui-bg)"
          stroke-width="0.75"
        />
      </g>

      <g aria-hidden="true" fill="none" stroke-linecap="round">
        <path
          v-for="r in rotalar"
          :key="r.id"
          :d="r.d"
          :stroke="aktifBolge === r.bolge ? 'var(--ui-text-highlighted)' : 'var(--viz-rota)'"
          :stroke-width="aktifBolge === r.bolge ? 2 : 1.25"
          :stroke-dasharray="r.hava ? '5 4' : undefined"
          :opacity="aktifBolge && aktifBolge !== r.bolge ? 0.25 : 0.8"
        />
      </g>

      <!-- Varış noktaları -->
      <g v-for="v in varislar" :key="v.bolge" aria-hidden="true">
        <rect :x="xy(v)[0] - 5" :y="xy(v)[1] - 5" width="10" height="10" rx="2" fill="var(--ui-text-highlighted)" stroke="var(--ui-bg)" stroke-width="2" />
        <text
          v-bind="{ x: etiketKonumu(v, 5, xy(v)).x, y: etiketKonumu(v, 5, xy(v)).y }"
          :text-anchor="etiketKonumu(v, 5, xy(v)).anchor"
          class="text-[13px] font-semibold"
          fill="var(--ui-text-highlighted)"
          stroke="var(--ui-bg-muted)"
          stroke-width="3"
          paint-order="stroke"
        >{{ yerAdi(v.bolge) }}</text>
      </g>

      <!-- Çıkış noktaları -->
      <g
        v-for="d in daireler"
        :key="d.bolge"
        tabindex="0"
        role="button"
        class="cursor-pointer outline-none"
        :aria-label="t('grafik.noktaAria', { bolge: yerAdi(d.bolge), n: d.tedarikciler.length, s: t(`seviye.${d.seviye}`), alim: para(d.alim) })"
        @mouseenter="grupIpucu($event, d)"
        @mousemove="konumla"
        @mouseleave="birak"
        @focus="grupIpucu($event, d)"
        @blur="birak"
      >
        <circle :cx="d.xy[0]" :cy="d.xy[1]" :r="d.r + 6" fill="transparent" />
        <circle
          :cx="d.xy[0]"
          :cy="d.xy[1]"
          :r="d.r"
          :fill="SEVIYE_VIZ_RENGI[d.seviye]"
          fill-opacity="0.88"
          :stroke="aktifBolge === d.bolge ? 'var(--ui-text-highlighted)' : 'var(--ui-bg)'"
          stroke-width="2"
        />
        <text
          v-bind="{ x: etiketKonumu(d.konum, d.r, d.xy).x, y: etiketKonumu(d.konum, d.r, d.xy).y }"
          :text-anchor="etiketKonumu(d.konum, d.r, d.xy).anchor"
          class="text-[12px] font-medium"
          fill="var(--ui-text-toned)"
          stroke="var(--ui-bg-muted)"
          stroke-width="3"
          paint-order="stroke"
        >{{ yerAdi(d.bolge) }}</text>
      </g>
    </svg>

    <GrafikIpucu v-bind="ipucu" />

    <div class="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-muted">
      <span v-for="s in sayilar" :key="s.seviye" class="flex items-center gap-1.5">
        <span class="inline-block size-3 rounded-full" :style="{ background: SEVIYE_VIZ_RENGI[s.seviye] }" />
        <UIcon :name="SEVIYE_IKONU[s.seviye]" class="size-3.5" />
        {{ t(`seviye.${s.seviye}`) }} ({{ s.sayi }})
      </span>
      <span class="flex items-center gap-1.5">
        <svg width="22" height="6" aria-hidden="true"><line x1="1" y1="3" x2="21" y2="3" stroke="var(--viz-rota)" stroke-width="1.5" /></svg>
        {{ t('grafik.deniz') }}
      </span>
      <span class="flex items-center gap-1.5">
        <svg width="22" height="6" aria-hidden="true"><line x1="1" y1="3" x2="21" y2="3" stroke="var(--viz-rota)" stroke-width="1.5" stroke-dasharray="5 4" /></svg>
        {{ t('grafik.hava') }}
      </span>
      <span class="text-xs">{{ t('grafik.haritaNotu') }}</span>
    </div>
    <p v-if="bilinmeyenler.length" class="mt-1 text-xs text-muted">
      {{ t('grafik.bilinmeyen') }} {{ bilinmeyenler.map(x => x.rota.cikis).join(', ') }}
    </p>
  </div>
</template>
