<script setup>
// Punto de decisión entre el Loop 1 y la respuesta final (a pedido del
// cliente, "como hace Google"): se muestra lo que la bibliografía permitió
// verificar y se pregunta cómo seguir. La respuesta final (Loop 2) se genera
// solo después de que el usuario elige.
import { computed, ref } from 'vue'
import { documentDownloadUrl } from '../../services/api.js'
import { EXTERNAL_ENGINE_LABEL } from '../../constants.js'

const props = defineProps({
  draft: { type: Object, required: true },
  // Opción en curso ('' | 'seguir' | 'complementar' | 'modelo'): bloquea los botones.
  busy: { type: String, default: '' },
  error: { type: String, default: '' },
})
const emit = defineEmits(['choose'])

const MODEL_LABELS = {
  plan_cuentas: 'plan de cuentas',
  estados_financieros: 'estado de situación financiera',
}
const MODEL_ACCEPT = '.pdf,.docx,.txt'
const MODEL_MAX_BYTES = 8 * 1024 * 1024

const loop1 = computed(() => props.draft.loop1 || {})
const verified = computed(() => loop1.value.verified_claims || [])
const missing = computed(() => loop1.value.missing_info || [])
const lacksInfo = computed(() => loop1.value.loop1_passed === false || missing.value.length > 0)
const modelLabel = computed(() => MODEL_LABELS[props.draft.model_kind] || '')

// Leyes de la bibliografía con archivo original disponible (máx. 3 distintas).
const downloadableLaws = computed(() => {
  const seen = new Set()
  const out = []
  for (const src of props.draft.sources_used || []) {
    if (!src.downloadable || !src.doc_id || seen.has(src.title)) continue
    seen.add(src.title)
    out.push(src)
    if (out.length === 3) break
  }
  return out
})

const modelFile = ref(null)
const modelFileError = ref('')
const fileInput = ref(null)

function onModelFile(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  modelFileError.value = ''
  if (!file) return
  const ext = `.${file.name.split('.').pop()?.toLowerCase() || ''}`
  if (!MODEL_ACCEPT.split(',').includes(ext)) {
    modelFileError.value = 'Adjunta un PDF, Word (.docx) o texto (.txt).'
    return
  }
  if (file.size > MODEL_MAX_BYTES) {
    modelFileError.value = 'El archivo supera el límite de 8 MB.'
    return
  }
  modelFile.value = file
}

function choose(mode) {
  if (props.busy) return
  emit('choose', {
    mode,
    kind: mode === 'modelo' ? props.draft.model_kind : '',
    file: mode === 'modelo' ? modelFile.value : null,
  })
}
</script>

<template>
  <div class="space-y-3">
    <div v-if="draft.refined_question" class="rounded-2xl border border-azulCorp/15 bg-azulCorp/5 px-4 py-3 text-xs text-azulCorp">
      <span class="text-[10px] font-bold uppercase tracking-wide text-azulCorp/70">Pregunta interpretada por la IA</span>
      <div class="mt-1 break-words leading-relaxed">{{ draft.refined_question }}</div>
    </div>

    <!-- Primera casilla: lo que dice la bibliografía -->
    <article class="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_8px_22px_rgba(15,23,42,0.05)] sm:p-5">
      <div class="mb-2 flex flex-wrap items-center gap-2">
        <span class="text-[11px] font-semibold uppercase tracking-wider text-oroOscuro">Primer análisis · bibliografía</span>
        <span v-if="draft.framework" class="max-w-full break-words rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
          Marco: {{ draft.framework }}
        </span>
      </div>

      <ul v-if="verified.length" class="space-y-1.5 text-sm leading-relaxed text-slate-800">
        <li v-for="(c, i) in verified" :key="i" class="break-words">
          <span class="font-bold text-verdeEsm">✓</span> {{ c.claim }}
          <span v-if="c.source" class="text-xs italic text-slate-500">({{ c.source }})</span>
        </li>
      </ul>
      <div v-else class="text-sm leading-relaxed text-slate-600">
        La bibliografía documentada no permitió verificar información suficiente para esta consulta.
      </div>

      <div v-if="missing.length" class="mt-3 rounded-xl border border-oro/30 bg-oro/5 px-3 py-2 text-xs text-oroOscuro">
        <div class="text-[10px] font-bold uppercase tracking-wide">Lo que falta en la bibliografía</div>
        <ul class="mt-1 list-disc space-y-0.5 pl-4">
          <li v-for="(m, i) in missing" :key="i" class="break-words">{{ m }}</li>
        </ul>
      </div>
    </article>

    <!-- Pregunta de decisión -->
    <section class="rounded-2xl border-2 border-oro/50 bg-gradient-to-br from-oro/10 via-white to-white p-4 shadow-sm sm:p-5">
      <div class="text-base font-extrabold text-azulCorp">¿Seguimos o prefieres otra opción?</div>
      <div class="mt-0.5 text-xs text-slate-500">Elige cómo continuar. La respuesta final se genera con la opción que escojas.</div>

      <div class="mt-3 grid gap-2.5">
        <button
          type="button"
          :disabled="!!busy"
          class="group flex w-full items-start gap-3 rounded-xl bg-gradient-to-r from-[#996515] to-[#D4AF37] px-4 py-3 text-left text-white shadow-md transition-all hover:-translate-y-0.5 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
          @click="choose('seguir')"
        >
          <span class="mt-0.5 text-lg leading-none">→</span>
          <span>
            <span class="block text-sm font-extrabold">{{ busy === 'seguir' ? 'Generando la respuesta final...' : 'Seguir con la respuesta final' }}</span>
            <span class="block text-xs text-white/90">Con lo verificado en la bibliografía documentada.</span>
          </span>
        </button>

        <button
          type="button"
          :disabled="!!busy"
          class="flex w-full items-start gap-3 rounded-xl border bg-white px-4 py-3 text-left transition-all hover:-translate-y-0.5 hover:border-oro hover:shadow-md disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
          :class="lacksInfo ? 'border-oro/70 ring-2 ring-oro/20' : 'border-slate-200'"
          @click="choose('complementar')"
        >
          <span class="mt-0.5 text-lg leading-none text-oroOscuro">⌕</span>
          <span>
            <span class="block text-sm font-bold text-azulCorp">
              {{ busy === 'complementar' ? 'Buscando información externa...' : `Completar con búsqueda externa (${EXTERNAL_ENGINE_LABEL})` }}
              <span v-if="lacksInfo" class="ml-1 rounded-full bg-oro/20 px-1.5 py-0.5 align-middle text-[9px] font-bold uppercase text-oroOscuro">Recomendado: faltan datos</span>
            </span>
            <span class="block text-xs text-slate-500">
              Cubre lo que falta en la bibliografía. Esa parte se marcará como <strong>no verificada</strong>.
            </span>
          </span>
        </button>

        <div v-if="modelLabel" class="rounded-xl border border-slate-200 bg-white px-4 py-3">
          <button
            type="button"
            :disabled="!!busy"
            class="flex w-full items-start gap-3 text-left disabled:cursor-not-allowed disabled:opacity-60"
            @click="choose('modelo')"
          >
            <span class="mt-0.5 text-lg leading-none text-oroOscuro">▤</span>
            <span>
              <span class="block text-sm font-bold text-azulCorp">
                {{ busy === 'modelo' ? 'Generando el modelo...' : `Generar un modelo de ${modelLabel} actualizado (PDF)` }}
              </span>
              <span class="block text-xs text-slate-500">
                Según la bibliografía. Si tienes uno anterior, adjúntalo abajo y se actualizará en vez de crear uno nuevo.
              </span>
            </span>
          </button>
          <div class="mt-2 flex flex-wrap items-center gap-2 pl-8 text-xs">
            <input ref="fileInput" type="file" :accept="MODEL_ACCEPT" class="hidden" @change="onModelFile" />
            <button
              type="button"
              :disabled="!!busy"
              class="rounded-lg border border-slate-300 bg-slate-50 px-2.5 py-1 font-semibold text-slate-600 hover:border-oro/60 hover:text-oroOscuro disabled:opacity-60"
              @click="fileInput?.click()"
            >
              {{ modelFile ? 'Cambiar documento anterior' : 'Adjuntar modelo anterior (opcional)' }}
            </button>
            <span v-if="modelFile" class="flex max-w-full items-center gap-1 rounded-lg border border-oro/30 bg-oro/5 px-2 py-1 font-medium text-oroOscuro">
              <span class="truncate">{{ modelFile.name }}</span>
              <button type="button" aria-label="Quitar documento" class="text-oroOscuro/70 hover:text-oroOscuro" @click="modelFile = null">×</button>
            </span>
            <span v-if="modelFileError" class="font-medium text-violetaIA">{{ modelFileError }}</span>
          </div>
        </div>

        <div v-if="downloadableLaws.length" class="rounded-xl border border-slate-200 bg-white px-4 py-3">
          <div class="text-xs font-bold text-azulCorp">¿Necesitas el texto de la norma? Descárgalo en PDF:</div>
          <div class="mt-1.5 flex flex-wrap gap-2">
            <a
              v-for="law in downloadableLaws"
              :key="law.doc_id"
              :href="documentDownloadUrl(law.doc_id)"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex max-w-full items-center gap-1.5 rounded-lg border border-oro/40 bg-oro/5 px-2.5 py-1.5 text-[11px] font-semibold text-oroOscuro transition-colors hover:bg-oro/15"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5 shrink-0">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10 5 5 5-5" /><path d="M12 15V3" />
              </svg>
              <span class="truncate">{{ law.title }}</span>
            </a>
          </div>
        </div>
      </div>

      <div v-if="error" class="mt-3 rounded-xl border border-violetaIA/20 bg-violetaIA/5 px-3 py-2 text-xs font-medium text-violetaIA">
        {{ error }}
      </div>
    </section>
  </div>
</template>
