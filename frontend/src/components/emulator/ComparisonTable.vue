<script setup>
// Comparativa operacional (contenido provisto por el cliente; es la misma tabla
// de la landing). Va al final de los gráficos de cada consulta.
const logoUrl = `${import.meta.env.BASE_URL}iaas-logo.png`

const modelos = [
  { nombre: 'Simulador Sostenible', detalle: '', propio: true },
  { nombre: 'ChatGPT', detalle: '(Estándar Generalista)' },
  { nombre: 'Claude', detalle: '(Analítico y Preciso)' },
  { nombre: 'Gemini', detalle: '(Información y Síntesis)' },
  { nombre: 'DeepSeek', detalle: '(Eficiencia)' },
]
const criterios = [
  ['Objetividad', [95, 85, 90, 82, 80]],
  ['Precisión de Reestructuración', [98, 80, 85, 78, 75]],
  ['Eficiencia (Consumo de Tokens)', [30, 90, 85, 92, 94]],
  ['Eficacia (Corrección)', [95, 85, 90, 82, 80]],
  ['Efectividad (Utilidad Gerencial)', [70, 85, 88, 80, 78]],
  ['Economía (Relación Costo/Beneficio)', [30, 90, 85, 92, 94]],
  ['Generación de Métricas Sostenibles ODS/ASG', [100, 0, 0, 0, 0]],
  ['Gestión y operacionalidad académica', [96, 88, 92, 85, 86]],
]
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-3 sm:p-5">
    <h4 class="text-center text-sm font-extrabold leading-snug text-azulCorp sm:text-base">
      Comparativa Operacional del Modelo<br />Simulador Sostenible + IA
    </h4>

    <div class="mt-3">
      <table class="w-full table-fixed border-collapse text-[9.5px] text-slate-800 sm:text-xs">
        <caption class="sr-only">Comparativa operacional del Simulador Sostenible + IA frente a ChatGPT, Claude, Gemini y DeepSeek</caption>
        <thead>
          <tr class="align-bottom">
            <th scope="col" class="w-[21%] border border-slate-300 px-1 py-2 text-left font-semibold sm:w-[24%] sm:px-2">Criterio / Evaluación</th>
            <th
              v-for="m in modelos"
              :key="m.nombre"
              scope="col"
              class="border border-slate-300 px-0.5 py-2 text-center font-semibold leading-tight sm:px-1.5"
              :class="m.propio ? 'bg-amber-50' : ''"
            >
              <img v-if="m.propio" :src="logoUrl" alt="" class="mx-auto mb-1 h-8 w-auto object-contain sm:h-10" />
              <span class="block text-azulCorp">{{ m.nombre }}</span>
              <span v-if="m.detalle" class="hidden font-normal text-slate-600 sm:block">{{ m.detalle }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="[criterio, valores] in criterios" :key="criterio" class="odd:bg-white even:bg-slate-50/60">
            <th scope="row" class="break-words border border-slate-300 px-1 py-1.5 text-left font-medium sm:px-2" lang="es">{{ criterio }}</th>
            <td
              v-for="(v, i) in valores"
              :key="i"
              class="border border-slate-300 px-0.5 py-1.5 text-center tabular-nums sm:px-1.5"
              :class="modelos[i].propio ? 'bg-amber-50 font-bold text-azulCorp' : ''"
            >
              {{ v }}%
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="mt-4 space-y-3 text-justify text-[11px] leading-relaxed text-slate-700 sm:text-xs">
      <div>
        <strong class="text-azulCorp">Nota técnica:</strong> El protocolo (<strong>AOPCCPS+IA</strong>) del Simulador Sostenible + IA, opera con una arquitectura de especialista, priorizando la precisión técnica, la gobernanza digital y la falsabilidad legal sobre la eficiencia lingüística.
      </div>
      <div>
        En contraste, las IA generalistas (como ChatGPT o Gemini) utilizan arquitecturas optimizadas para la velocidad de respuesta, el uso reducido de tokens y la comunicación conversacional, lo que las hace más eficaces en métricas de "economía" y "eficiencia" pero menos precisas en la reestructuración metodológica.
      </div>
    </div>
  </section>
</template>
