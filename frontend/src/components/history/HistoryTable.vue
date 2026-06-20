<script setup>
const props = defineProps({
  entries: Array
})

defineEmits(['select'])

function getPercent(entry) {
  return Math.max(0, Math.min(100, Number(entry?.percent || 0)))
}

function hasContextAlert(entry) {
  return Boolean(entry?.cvFailed) || entry?.cvStatus === 'failed' || getPercent(entry) < 100
}

function complianceLabel(entry) {
  const percent = getPercent(entry)
  return hasContextAlert(entry) ? `${percent}% Alerta` : '100% Aprobado'
}
</script>

<template>
  <div>
    <div class="hidden overflow-x-auto rounded-xl shadow-sm md:block">
      <table class="min-w-full divide-y divide-slate-200 overflow-hidden rounded-xl bg-white">
      <thead>
        <tr>
          <th class="bg-slate-50 p-4 text-left text-xs font-semibold uppercase text-slate-500">Expediente</th>
          <th class="bg-slate-50 p-4 text-left text-xs font-semibold uppercase text-slate-500">Fecha</th>
          <th class="bg-slate-50 p-4 text-left text-xs font-semibold uppercase text-slate-500">Entidad</th>
          <th class="bg-slate-50 p-4 text-left text-xs font-semibold uppercase text-slate-500">Solicitud</th>
          <th class="bg-slate-50 p-4 text-left text-xs font-semibold uppercase text-slate-500">Cumplimiento</th>
          <th class="bg-slate-50 p-4 text-left text-xs font-semibold uppercase text-slate-500">Acciones</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-200 text-sm text-slate-700">
        <tr
          v-for="(entry, i) in props.entries"
          :key="i"
          class="cursor-pointer odd:bg-white even:bg-slate-50/50 transition-colors hover:bg-oro/5"
          @click="$emit('select', entry)"
        >
          <td class="p-4 font-medium text-azulCorp">{{ entry.id }}</td>
          <td class="p-4">{{ entry.date }}</td>
          <td class="p-4">{{ entry.entity }}</td>
          <td class="max-w-85 truncate p-4 text-slate-600">{{ entry.request }}</td>
          <td class="p-4">
            <div class="flex items-center gap-3">
              <span
                class="inline-flex h-8 w-8 items-center justify-center rounded-full text-[10px] font-semibold"
                :class="hasContextAlert(entry) ? 'bg-oro/15 text-oroOscuro' : 'bg-verdeEsm/15 text-verdeEsm'"
              >
                {{ getPercent(entry) }}%
              </span>
              <div class="min-w-0 flex-1">
                <div class="mb-1 h-1.5 w-full rounded-full bg-slate-200">
                <div
                  class="h-1.5 rounded-full"
                  :class="hasContextAlert(entry) ? 'bg-oro' : 'bg-verdeEsm'"
                  :style="{ width: getPercent(entry) + '%' }"
                ></div>
              </div>
                <p
                  class="truncate text-xs font-medium"
                  :class="hasContextAlert(entry) ? 'text-oroOscuro' : 'text-verdeEsm'"
                >
                  {{ complianceLabel(entry) }}
                </p>
              </div>
            </div>
          </td>
          <td class="p-4">
            <div class="flex items-center gap-2">
              <button
                class="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-azulCorp"
                title="Ver detalle"
                @click.stop="$emit('select', entry)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              </button>

              <button
                class="rounded-lg p-2 text-oro transition-colors hover:bg-oro/10 hover:text-oroOscuro"
                title="Descargar PDF"
                @click.stop
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

    <div class="space-y-3 md:hidden">
      <article
        v-for="(entry, i) in props.entries"
        :key="`mobile-${i}`"
        class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm cursor-pointer transition-colors hover:border-oro/30"
        @click="$emit('select', entry)"
      >
        <div class="mb-3 flex items-start justify-between gap-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ entry.id }}</p>
            <h3 class="mt-0.5 text-sm font-semibold text-azulCorp">{{ entry.entity }}</h3>
          </div>
          <span class="text-xs text-slate-500">{{ entry.date }}</span>
        </div>

        <p class="mb-3 text-sm text-slate-600">{{ entry.request }}</p>

        <div class="mb-3 flex items-center gap-3">
          <span
            class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold"
            :class="hasContextAlert(entry) ? 'bg-oro/15 text-oroOscuro' : 'bg-verdeEsm/15 text-verdeEsm'"
          >
            {{ complianceLabel(entry) }}
          </span>
          <div class="h-1.5 flex-1 rounded-full bg-slate-200">
            <div
              class="h-1.5 rounded-full"
              :class="hasContextAlert(entry) ? 'bg-oro' : 'bg-verdeEsm'"
              :style="{ width: getPercent(entry) + '%' }"
            ></div>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2">
          <button
            class="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-azulCorp"
            title="Ver detalle"
            @click.stop="$emit('select', entry)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </button>

          <button
            class="rounded-lg p-2 text-oro transition-colors hover:bg-oro/10 hover:text-oroOscuro"
            title="Descargar PDF"
            @click.stop
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
