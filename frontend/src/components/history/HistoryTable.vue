<script setup>
import { ref } from 'vue'
import { exportSimulation } from '../../services/api.js'

const props = defineProps({
  entries: Array
})

defineEmits(['select'])

const downloadError = ref('')

const fmtInt = (n) => Number(n || 0).toLocaleString('es')
const fmtUsd = (n) => {
  const v = Number(n || 0)
  if (v === 0) return '—'
  return v < 0.01 ? `$${v.toFixed(4)}` : `$${v.toFixed(3)}`
}
// Los expedientes anteriores a las métricas de energía quedaron en 0.
const fmtEnergy = (n) => (Number(n || 0) > 0 ? `${Number(n).toFixed(2)} Wh` : '—')

function triggerDownload(payload, filename) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function downloadEntry(entry) {
  downloadError.value = ''
  try {
    const record = await exportSimulation(entry.id)
    triggerDownload(record, `memoria-tecnica-${entry.id}.json`)
  } catch (error) {
    downloadError.value = error.message || 'No se pudo descargar'
  }
}
</script>

<template>
  <div>
    <p v-if="downloadError" class="mb-3 rounded-xl border border-oro/40 bg-oro/5 px-3 py-2 text-xs font-medium text-oroOscuro">
      {{ downloadError }}
    </p>
    <!-- lg (1024px), no md (768px): con 8 columnas la tabla no cabe cómoda en un
    tablet en portrait — el breakpoint md salía con scroll horizontal. -->
    <div class="hidden overflow-x-auto rounded-2xl border border-slate-200/80 lg:block">
      <table class="min-w-full divide-y divide-slate-200 overflow-hidden rounded-2xl bg-white/80">
      <thead>
        <tr>
          <th class="bg-slate-50/80 px-4 py-3.5 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">Expediente</th>
          <th class="bg-slate-50/80 px-4 py-3.5 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">Fecha</th>
          <th class="bg-slate-50/80 px-4 py-3.5 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">Entidad</th>
          <th class="bg-slate-50/80 px-4 py-3.5 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">Solicitud</th>
          <th class="bg-slate-50/80 px-4 py-3.5 text-right text-[10px] font-bold uppercase tracking-wider text-slate-500">Tokens</th>
          <th class="bg-slate-50/80 px-4 py-3.5 text-right text-[10px] font-bold uppercase tracking-wider text-slate-500">Costo</th>
          <th class="bg-slate-50/80 px-4 py-3.5 text-right text-[10px] font-bold uppercase tracking-wider text-slate-500">Energía est.</th>
          <th class="bg-slate-50/80 px-4 py-3.5 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">Acciones</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-200 text-sm text-slate-700">
        <tr
          v-for="(entry, i) in props.entries"
          :key="i"
          class="cursor-pointer odd:bg-white/80 even:bg-slate-50/50 transition-colors hover:bg-oro/5"
          @click="$emit('select', entry)"
        >
          <td class="p-4 font-medium text-azulCorp">{{ entry.id }}</td>
          <td class="p-4">{{ entry.date }}</td>
          <td class="p-4">{{ entry.entity }}</td>
          <td class="max-w-[18rem] truncate p-4 text-slate-600">{{ entry.request }}</td>
          <td class="whitespace-nowrap p-4 text-right tabular-nums">{{ fmtInt(entry.tokens) }}</td>
          <td class="whitespace-nowrap p-4 text-right tabular-nums">{{ fmtUsd(entry.cost) }}</td>
          <td class="whitespace-nowrap p-4 text-right tabular-nums text-verdeEsm">{{ fmtEnergy(entry.energy) }}</td>
          <td class="p-4">
            <div class="flex items-center gap-2">
              <button
                class="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-azulCorp"
                title="Ver detalle"
                aria-label="Ver detalle"
                @click.stop="$emit('select', entry)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              </button>

              <button
                class="rounded-lg p-2 text-oro transition-colors hover:bg-oro/10 hover:text-oroOscuro"
                title="Descargar memoria técnica"
                aria-label="Descargar memoria técnica"
                @click.stop="downloadEntry(entry)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <path d="M14 2v6h6" />
                  <path d="M12 12v6" />
                  <path d="m9.5 15.5 2.5 2.5 2.5-2.5" />
                </svg>
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    </div>

    <div class="space-y-3 lg:hidden">
      <article
        v-for="(entry, i) in props.entries"
        :key="`mobile-${i}`"
        class="cursor-pointer rounded-2xl border border-slate-200/80 bg-white/80 p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:border-oro/30 hover:shadow-md"
        @click="$emit('select', entry)"
      >
        <div class="mb-3 flex items-start justify-between gap-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ entry.id }}</p>
            <h3 class="mt-0.5 text-sm font-semibold text-azulCorp">{{ entry.entity }}</h3>
          </div>
          <span class="text-xs text-slate-500">{{ entry.date }}</span>
        </div>

        <p class="mb-3 break-words text-sm text-slate-600">{{ entry.request }}</p>

        <div class="mb-3 flex flex-wrap items-center gap-2 text-[11px] font-semibold">
          <span class="rounded-full bg-slate-100 px-2.5 py-1 text-slate-600">{{ fmtInt(entry.tokens) }} tokens</span>
          <span class="rounded-full bg-oro/15 px-2.5 py-1 text-oroOscuro">{{ fmtUsd(entry.cost) }}</span>
          <span class="rounded-full bg-verdeEsm/15 px-2.5 py-1 text-verdeEsm">{{ fmtEnergy(entry.energy) }}</span>
        </div>

        <div class="flex items-center justify-end gap-2">
          <button
            class="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-azulCorp"
            title="Ver detalle"
            aria-label="Ver detalle"
            @click.stop="$emit('select', entry)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </button>

          <button
            class="rounded-lg p-2 text-oro transition-colors hover:bg-oro/10 hover:text-oroOscuro"
            title="Descargar memoria técnica"
            aria-label="Descargar memoria técnica"
            @click.stop="downloadEntry(entry)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <path d="M14 2v6h6" />
              <path d="M12 12v6" />
              <path d="m9.5 15.5 2.5 2.5 2.5-2.5" />
            </svg>
          </button>
        </div>
      </article>
    </div>
  </div>
</template>
