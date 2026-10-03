<script setup>
import { computed, ref } from 'vue'
import { exportSimulation } from '../../services/api.js'
import SustainabilityPanel from './SustainabilityPanel.vue'
import { FEEDBACK_FORM_URL } from '../../constants.js'

const props = defineProps({
  result: { type: Object, required: true },
})

const ENTITY_LABELS = { publica: 'Pública', privada: 'Privada', mixta: 'Mixta' }

const loop1 = computed(() => props.result.loop1 || {})
const loop2 = computed(() => props.result.loop2 || {})
const entity = computed(() => ENTITY_LABELS[props.result.entity_type] || props.result.entity_type)

const consultedSources = computed(() => {
  const titles = (props.result.sources_used || []).map((s) => s.title)
  return [...new Set(titles)]
})

const pruningPercent = computed(() => Math.round((loop2.value.pruning_ratio || 0) * 100))

const verification = computed(() => ({
  verified: loop1.value.verified_claims?.length || 0,
  discarded: loop1.value.discarded_claims?.length || 0,
}))

// "Tema no resuelto": el Loop 1 no pudo verificar nada contra la bibliografía,
// o el Loop 2 marcó la respuesta como no concluyente. En ambos casos se
// ofrece el buzón de sugerencias de arriba.
const isUnresolved = computed(() => loop1.value.loop1_passed === false || loop2.value.condition_met === false)

const isDownloading = ref(false)
const downloadError = ref('')
const shareFeedback = ref('')

async function downloadAnswer() {
  if (!props.result.expediente_id) return
  isDownloading.value = true
  downloadError.value = ''
  try {
    const fullRecord = await exportSimulation(props.result.expediente_id)
    const blob = new Blob([JSON.stringify(fullRecord, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `memoria-tecnica-${props.result.expediente_id}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (error) {
    downloadError.value = error.message || 'No se pudo descargar'
  } finally {
    isDownloading.value = false
  }
}

function buildShareText() {
  return [props.result.refined_question, '', loop2.value.final_answer, props.result.expediente_id ? `\nExpediente: ${props.result.expediente_id}` : '']
    .filter(Boolean)
    .join('\n')
}

// Compartir: libre para todos (sin cuenta paga), igual que descargar — es
// solo el texto de la respuesta, no cuesta nada dejarlo libre. En celular con
// soporte de Web Share (navigator.share), un solo toque abre el panel nativo
// del sistema, que ya lista WhatsApp/correo/lo que tenga instalado — "como lo
// hacen las apps normalmente". En desktop, donde la mayoría de los
// navegadores no lo soportan, se muestra un menú propio con los mismos tres
// canales de siempre: WhatsApp Web, correo (mailto) y copiar.
const showShareMenu = ref(false)

async function shareAnswer() {
  shareFeedback.value = ''
  if (navigator.share) {
    try {
      await navigator.share({ title: 'Inglobals — Simulador Sostenible', text: buildShareText() })
    } catch {
      // El usuario cerró el panel nativo de compartir — no es un error.
    }
    return
  }
  showShareMenu.value = !showShareMenu.value
}

function shareViaWhatsapp() {
  window.open(`https://wa.me/?text=${encodeURIComponent(buildShareText())}`, '_blank', 'noopener')
  showShareMenu.value = false
}

function shareViaEmail() {
  const subject = 'Respuesta del Simulador Sostenible — Inglobals'
  window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(buildShareText())}`
  showShareMenu.value = false
}

async function copyShareText() {
  try {
    await navigator.clipboard.writeText(buildShareText())
    shareFeedback.value = 'Copiado al portapapeles'
  } catch {
    shareFeedback.value = 'No se pudo copiar'
  }
  showShareMenu.value = false
  setTimeout(() => { shareFeedback.value = '' }, 2500)
}
</script>

<template>
  <div class="space-y-3">
    <!-- Paso 0: la IA reformula la consulta cruda en una pregunta más precisa
    antes de buscar en la bibliografía (no es parte del Loop 1/Loop 2 del
    paper, se agregó a pedido del cliente). -->
    <div
      v-if="result.refined_question"
      class="rounded-2xl border border-azulCorp/15 bg-azulCorp/5 px-4 py-3 text-xs text-azulCorp"
    >
      <span class="text-[10px] font-bold uppercase tracking-wide text-azulCorp/70">Pregunta interpretada por la IA</span>
      <div class="mt-1 break-words leading-relaxed">
        {{ result.refined_question }}<sup v-if="isUnresolved" class="font-bold text-oroOscuro">*</sup>
      </div>
    </div>

    <!-- Tema no resuelto: ni el Loop 1 pudo verificar nada contra la
    bibliografía, ni el Loop 2 dio una respuesta concluyente. Se ofrece un
    buzón de sugerencias (formulario) para que el equipo revise el caso. -->
    <div
      v-if="isUnresolved"
      class="rounded-2xl border border-oro/40 bg-oro/5 px-4 py-3 text-xs font-medium text-oroOscuro"
    >
      <p>
        <template v-if="loop1.loop1_passed === false">
          El Loop 1 no pudo verificar información suficiente en la bibliografía documentada, así que la respuesta se limita a
          lo comprobable (falsabilidad 3/3).
        </template>
        <template v-else>
          El Loop 2 marcó esta respuesta como no concluyente según el protocolo.
        </template>
        <sup>*</sup>
      </p>
      <div class="mt-2 flex flex-wrap items-center justify-between gap-2 border-t border-oro/20 pt-2">
        <span class="text-[11px] font-semibold text-oroOscuro/80">* Tema no resuelto</span>
        <a
          :href="FEEDBACK_FORM_URL"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center gap-1.5 rounded-lg bg-oroOscuro px-3 py-1.5 text-[11px] font-bold text-white transition-colors hover:bg-oroOscuro/90"
        >
          Enviar sugerencia
        </a>
      </div>
    </div>

    <!-- Respuesta final (Loop 2) -->
    <article class="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_8px_22px_rgba(15,23,42,0.05)] sm:p-5">
      <div class="mb-3 flex flex-wrap items-center gap-2">
        <span class="text-[11px] font-semibold uppercase tracking-wider text-oroOscuro">Respuesta</span>
        <span v-if="entity" class="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
          Entidad: {{ entity }}
        </span>
        <span
          v-if="result.framework"
          class="max-w-full break-words rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600"
        >
          Marco: {{ result.framework }}
        </span>
      </div>

      <div class="break-words whitespace-pre-line text-sm leading-relaxed text-slate-800">{{ loop2.final_answer }}</div>

      <div class="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1.5 border-t border-slate-100 pt-3 text-[11px] text-slate-500">
        <span
          class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide"
          :class="loop2.condition_met ? 'bg-verdeEsm/15 text-verdeEsm' : 'bg-oro/15 text-oroOscuro'"
        >
          {{ loop2.condition_met ? 'Estado = verdadero' : 'Condición no cumplida' }}
        </span>
        <span>{{ loop2.words }} palabras<template v-if="loop2.max_words"> (máx. {{ loop2.max_words }})</template></span>
        <span v-if="loop2.draft_words && pruningPercent > 0">Poda: {{ pruningPercent }}% menos que el borrador lógico</span>
        <span v-if="result.expediente_id" class="ml-auto font-medium text-slate-400">{{ result.expediente_id }}</span>
      </div>
    </article>

    <!-- Descargar y Compartir: libres para todos, sin cuenta paga. -->
    <div class="flex flex-wrap items-center gap-2 text-[11px]">
      <button
        @click="downloadAnswer"
        :disabled="isDownloading"
        class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 font-semibold text-slate-600 transition-colors hover:border-oro/40 hover:text-oroOscuro disabled:cursor-not-allowed disabled:opacity-50"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <path d="m7 10 5 5 5-5" />
          <path d="M12 15V3" />
        </svg>
        {{ isDownloading ? 'Descargando...' : 'Descargar' }}
      </button>

      <!-- Compartir: en celular con Web Share, shareAnswer() abre el panel
      nativo directo (sin menú propio). En desktop, sin esa API, muestra este
      menú con WhatsApp / correo / copiar. -->
      <div class="relative">
        <button
          @click="shareAnswer"
          class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 font-semibold text-slate-600 transition-colors hover:border-oro/40 hover:text-oroOscuro"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5">
            <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" />
            <path d="m8.59 13.51 6.83 3.98M15.41 6.51 8.59 10.49" />
          </svg>
          Compartir
        </button>

        <button
          v-if="showShareMenu"
          aria-hidden="true"
          tabindex="-1"
          class="fixed inset-0 z-10 cursor-default"
          @click="showShareMenu = false"
        ></button>
        <div
          v-if="showShareMenu"
          class="absolute left-0 top-full z-20 mt-1.5 w-44 overflow-hidden rounded-xl border border-slate-200 bg-white py-1 shadow-lg"
        >
          <button
            @click="shareViaWhatsapp"
            class="flex w-full items-center gap-2 px-3 py-2 text-left text-slate-600 hover:bg-slate-50 hover:text-oroOscuro"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-3.5 w-3.5 shrink-0">
              <path d="M12.04 2c-5.46 0-9.9 4.44-9.9 9.9 0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.9 9.9 0 0 0 4.79 1.22h.01c5.46 0 9.9-4.44 9.9-9.9 0-2.64-1.03-5.12-2.9-6.98A9.82 9.82 0 0 0 12.04 2m0 1.67c2.2 0 4.26.86 5.82 2.4a8.2 8.2 0 0 1 2.42 5.83c0 4.54-3.7 8.23-8.24 8.23a8.2 8.2 0 0 1-4.19-1.15l-.3-.18-3.12.82.83-3.04-.2-.31a8.18 8.18 0 0 1-1.26-4.37c0-4.54 3.7-8.23 8.24-8.23m-4.42 4.72c-.16 0-.42.06-.64.3-.22.24-.84.82-.84 2s.86 2.32.98 2.48c.12.16 1.67 2.65 4.13 3.6 2.04.8 2.46.64 2.9.6.44-.04 1.42-.58 1.62-1.14.2-.56.2-1.04.14-1.14-.06-.1-.22-.16-.46-.28s-1.42-.7-1.64-.78c-.22-.08-.38-.12-.54.12s-.62.78-.76.94c-.14.16-.28.18-.52.06-.24-.12-1-.37-1.9-1.17-.7-.63-1.18-1.4-1.32-1.64-.14-.24 0-.36.1-.5.14-.18.27-.3.4-.45.13-.15.17-.26.26-.43.09-.17.04-.32-.02-.45-.06-.12-.54-1.32-.75-1.8-.2-.47-.4-.4-.55-.4" />
            </svg>
            WhatsApp
          </button>
          <button
            @click="shareViaEmail"
            class="flex w-full items-center gap-2 px-3 py-2 text-left text-slate-600 hover:bg-slate-50 hover:text-oroOscuro"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5 shrink-0">
              <rect x="2" y="4" width="20" height="16" rx="2" /><path d="m22 6-10 7L2 6" />
            </svg>
            Correo
          </button>
          <button
            @click="copyShareText"
            class="flex w-full items-center gap-2 px-3 py-2 text-left text-slate-600 hover:bg-slate-50 hover:text-oroOscuro"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3.5 w-3.5 shrink-0">
              <rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            Copiar
          </button>
        </div>
      </div>

      <span v-if="shareFeedback" class="text-slate-400">{{ shareFeedback }}</span>
      <span v-if="downloadError" class="font-medium text-oroOscuro">{{ downloadError }}</span>
    </div>

    <!-- Trazabilidad del Loop 1 — siempre expandida, el cliente pidió no tener
    que hacer clic para verla completa. -->
    <details open class="group rounded-2xl border border-slate-200 bg-slate-50/70 p-4 sm:p-5">
      <summary class="cursor-pointer list-none text-xs font-bold text-azulCorp">
        <span class="mr-1 inline-block text-slate-400 transition-transform group-open:rotate-90">▸</span>
        Trazabilidad del Loop 1 <span class="font-normal text-slate-500">— filtro filosófico, técnico y epistemológico</span>
      </summary>

      <div class="mt-4 space-y-4 text-xs leading-relaxed text-slate-700">
        <div v-if="loop1.ontological" class="grid gap-3 sm:grid-cols-2">
          <div>
            <div class="mb-0.5 text-[10px] font-bold uppercase tracking-wide text-slate-500">Ontológico</div>
            <div class="break-words">{{ loop1.ontological }}</div>
          </div>
          <div v-if="loop1.phenomenological">
            <div class="mb-0.5 text-[10px] font-bold uppercase tracking-wide text-slate-500">Fenomenológico</div>
            <div class="break-words">{{ loop1.phenomenological }}</div>
          </div>
        </div>

        <div v-if="loop1.verified_claims?.length">
          <div class="mb-1 text-[10px] font-bold uppercase tracking-wide text-verdeEsm">Verificadas (falsabilidad 3/3)</div>
          <ul class="space-y-1.5">
            <li v-for="(c, i) in loop1.verified_claims" :key="`v${i}`" class="break-words">
              <span class="font-bold text-verdeEsm">✓</span> {{ c.claim }}
              <span v-if="c.source" class="italic text-slate-500">({{ c.source }})</span>
            </li>
          </ul>
        </div>

        <div v-if="loop1.discarded_claims?.length">
          <div class="mb-1 text-[10px] font-bold uppercase tracking-wide text-violetaIA">Descartadas</div>
          <ul class="space-y-1.5">
            <li v-for="(c, i) in loop1.discarded_claims" :key="`d${i}`" class="break-words">
              <span class="font-bold text-violetaIA">✗</span> {{ c.claim }}
              <span v-if="c.reason" class="italic text-slate-500">— {{ c.reason }}</span>
            </li>
          </ul>
        </div>

        <div v-if="loop1.missing_info?.length">
          <div class="mb-1 text-[10px] font-bold uppercase tracking-wide text-oroOscuro">Información faltante</div>
          <ul class="list-disc space-y-1 pl-4">
            <li v-for="(m, i) in loop1.missing_info" :key="`m${i}`" class="break-words">{{ m }}</li>
          </ul>
        </div>

        <div v-if="consultedSources.length">
          <div class="mb-1 text-[10px] font-bold uppercase tracking-wide text-slate-500">Bibliografía consultada</div>
          <div class="break-words text-slate-500">{{ consultedSources.join(' · ') }}</div>
        </div>
      </div>
    </details>

    <SustainabilityPanel v-if="result.sustainability" :sustainability="result.sustainability" :verification="verification" />
  </div>
</template>
