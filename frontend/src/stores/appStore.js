import { reactive, ref } from 'vue'

export const currentView = ref('emulator')

export const entityType = ref('publica')
export const activeLaws = ref([])

export const simulationStatus = ref('idle')

export const dadVariables = reactive({
  Cs: { label: 'Cs',  name: 'Costo',               status: 'idle' },
  Cv: { label: 'Cv',  name: 'Contexto Venezolano', status: 'idle' },
  CS: { label: 'CS',  name: 'Cumplimiento Sostenible', status: 'idle' },
  GT: { label: 'GT',  name: 'Gestión Tributaria',  status: 'idle' },
  NI: { label: 'NI',  name: 'Normativa Internacional', status: 'idle' },
})

export const simulationHistory = ref([])
export const documents = ref([])

export function setView(view) {
  currentView.value = view
}

export function setEntityType(type) {
  entityType.value = type
}

export function setActiveLaws(laws) {
  activeLaws.value = laws
}

export function resetDadVariables() {
  for (const key of Object.keys(dadVariables)) {
    dadVariables[key].status = 'idle'
  }
}

export function setDadVariableStatus(key, status) {
  if (dadVariables[key]) {
    dadVariables[key].status = status
  }
}

export function addToHistory(entry) {
  simulationHistory.value.push(entry)
}
