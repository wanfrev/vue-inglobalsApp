<script setup>
defineProps({
  entries: Array
})

defineEmits(['select'])
</script>

<template>
  <div class="overflow-x-auto rounded-lg border border-slate-700">
    <table class="w-full text-left text-sm">
      <thead class="border-b border-slate-700 bg-slate-800 text-xs uppercase tracking-wider text-slate-400">
        <tr>
          <th class="px-4 py-3">Fecha</th>
          <th class="px-4 py-3">Entidad</th>
          <th class="px-4 py-3">Solicitud</th>
          <th class="px-4 py-3">Cumplimiento</th>
          <th class="px-4 py-3">Acciones</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-800">
        <tr
          v-for="(entry, i) in entries"
          :key="i"
          class="cursor-pointer transition-colors hover:bg-slate-800/50"
          @click="$emit('select', entry)"
        >
          <td class="px-4 py-3 text-slate-300">{{ entry.date }}</td>
          <td class="px-4 py-3 text-slate-300">{{ entry.entity }}</td>
          <td class="max-w-[200px] truncate px-4 py-3 text-slate-400">{{ entry.request }}</td>
          <td class="px-4 py-3">
            <div class="flex items-center gap-2">
              <div class="h-1.5 w-20 rounded-full bg-slate-700">
                <div
                  class="h-1.5 rounded-full"
                  :class="entry.percent >= 70 ? 'bg-emerald' : 'bg-crimson'"
                  :style="{ width: entry.percent + '%' }"
                ></div>
              </div>
              <span class="text-xs text-slate-400">{{ entry.percent }}%</span>
            </div>
          </td>
          <td class="px-4 py-3">
            <button
              class="rounded border border-slate-600 px-2 py-1 text-[11px] text-slate-300 transition-colors hover:bg-slate-700"
              @click.stop
            >
              Exportar PDF
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
