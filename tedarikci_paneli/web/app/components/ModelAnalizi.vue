<script setup lang="ts">
// Modelin bir haber (olay) için yaptığı çıkarım. Olaylar sayfasında, olayın genel bilgilerinden sonra gösterilir.
// Bütün metinler düz metin olarak gösterilir; kaynak bağlantıları şemada https ile sınırlıdır.
const props = defineProps<{ rapor: ModelCikarimi, tedarikciler: RiskliTedarikci[] }>()

const tedarikciAdi = computed(() => new Map(props.tedarikciler.map(t => [t.id, `${t.firma} · ${t.parca}`])))
const SIRA: Record<Seviye, number> = { yuksek: 0, orta: 1, dusuk: 2 }
const bulgular = computed(() => [...props.rapor.bulgular].sort((a, b) => SIRA[a.seviye] - SIRA[b.seviye]))
const oneriler = computed(() => [...props.rapor.oneriler].sort((a, b) => SIRA[a.oncelik] - SIRA[b.oncelik]))
</script>

<template>
  <UCard class="ring-1 ring-primary/30">
    <template #header>
      <div class="min-w-0 space-y-1">
        <p class="flex items-center gap-1.5 text-sm font-medium text-primary">
          <UIcon name="i-lucide-bot" class="size-4" />
          Model çıkarımı · {{ rapor.model.ad }} {{ rapor.model.surum }}
        </p>
        <h3 class="text-lg font-semibold text-highlighted">{{ rapor.baslik }}</h3>
        <p class="text-xs text-muted">{{ tarihSaatBicimi(rapor.olusturma) }}</p>
      </div>
    </template>

    <div class="space-y-5">
      <div class="grid gap-3 grid-cols-3">
        <div class="rounded-md bg-elevated/50 p-3">
          <p class="text-xs text-muted">Genel değerlendirme</p>
          <SeviyeRozeti :seviye="rapor.genelDegerlendirme.seviye" buyuk class="mt-1.5" />
        </div>
        <div class="rounded-md bg-elevated/50 p-3">
          <p class="text-xs text-muted">Risk skoru</p>
          <p class="mt-1 text-xl font-semibold text-highlighted">
            {{ rapor.genelDegerlendirme.skor !== undefined ? `${sayiBicimi(rapor.genelDegerlendirme.skor)} / 100` : '—' }}
          </p>
        </div>
        <div class="rounded-md bg-elevated/50 p-3">
          <p class="text-xs text-muted">Modelin güveni</p>
          <p class="mt-1 text-xl font-semibold text-highlighted">
            {{ rapor.genelDegerlendirme.guven !== undefined ? `%${Math.round(rapor.genelDegerlendirme.guven * 100)}` : '—' }}
          </p>
        </div>
      </div>

      <div>
        <h4 class="text-sm font-semibold text-highlighted">Özet</h4>
        <p class="mt-1 text-default whitespace-pre-line">{{ rapor.ozet }}</p>
      </div>

      <div v-if="bulgular.length">
        <h4 class="text-sm font-semibold text-highlighted">Bulgular ({{ bulgular.length }})</h4>
        <ul class="mt-1 divide-y divide-default">
          <li v-for="(b, i) in bulgular" :key="i" class="py-3 space-y-1.5">
            <div class="flex items-start justify-between gap-3">
              <p class="font-medium text-highlighted">{{ b.baslik }}</p>
              <SeviyeRozeti :seviye="b.seviye" class="shrink-0" />
            </div>
            <p class="text-sm text-default whitespace-pre-line">{{ b.aciklama }}</p>
            <div v-if="b.tedarikciIdleri.length" class="flex flex-wrap gap-1.5 pt-1">
              <UBadge
                v-for="tid in b.tedarikciIdleri"
                :key="tid"
                color="neutral"
                variant="outline"
                size="sm"
                icon="i-lucide-building-2"
              >
                {{ tedarikciAdi.get(tid) ?? `Tedarikçi #${tid}` }}
              </UBadge>
            </div>
          </li>
        </ul>
      </div>

      <div v-if="oneriler.length">
        <h4 class="text-sm font-semibold text-highlighted">Öneriler</h4>
        <ul class="mt-2 space-y-2">
          <li v-for="(o, i) in oneriler" :key="i" class="flex items-start gap-3">
            <SeviyeRozeti :seviye="o.oncelik" class="shrink-0 mt-0.5" />
            <p class="text-sm text-default">{{ o.metin }}</p>
          </li>
        </ul>
      </div>

      <div v-if="rapor.kaynaklar.length">
        <h4 class="text-sm font-semibold text-highlighted">Kaynaklar</h4>
        <ul class="mt-1 space-y-1 text-sm">
          <li v-for="(k, i) in rapor.kaynaklar" :key="i" class="flex items-center gap-1.5 min-w-0">
            <UIcon name="i-lucide-external-link" class="size-3.5 text-muted shrink-0" />
            <ULink :to="k.url" target="_blank" rel="noopener noreferrer" class="text-primary truncate">{{ k.ad }}</ULink>
          </li>
        </ul>
      </div>

      <p class="text-xs text-muted">
        Bu değerlendirme {{ rapor.model.ad }} tarafından üretilmiştir; karar vermeden önce bulguları kaynaklarıyla kontrol edin.
      </p>
    </div>
  </UCard>
</template>
