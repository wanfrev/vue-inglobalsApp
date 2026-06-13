import { reactive, ref } from 'vue'

export const currentView = ref('emulator')

export const entityType = ref('publica')
export const framework = ref('NIA 230')
export const activeLaws = ref([])

export const simulationStatus = ref('idle')
export const simulationResult = ref(null)

export const dadVariables = reactive({
  Cs: { label: 'Cs',  name: 'Ciencias Sociales / Juicio Profesional', status: 'idle' },
  Cv: { label: 'Cv',  name: 'Contexto Venezolano / Sostenibilidad', status: 'idle' },
  CS: { label: 'CS',  name: 'Capital Social / Estructuración', status: 'idle' },
  GT: { label: 'GT',  name: 'Gestión Tecnológica / IA', status: 'idle' },
  NI: { label: 'NI',  name: 'Normas Internacionales', status: 'idle' },
})

export const simulationHistory = ref([])
export const documents = ref([])

export function setView(view) {
  currentView.value = view
}

export function setEntityType(type) {
  entityType.value = type
}

export function setFramework(fw) {
  framework.value = fw
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

export function updateDadVariablesFromResult(result) {
  if (!result || !result.criteria) return
  
  const criteriaMap = {
    Cs: 'Cs',
    Cv: 'Cv',
    CS: 'CS',
    GT: 'GT',
    NI: 'NI',
  }
  
  for (const [backendKey, storeKey] of Object.entries(criteriaMap)) {
    const criterion = result.criteria[backendKey]
    if (criterion && dadVariables[storeKey]) {
      dadVariables[storeKey].status = criterion.status === 'passed' ? 'success' : 'error'
    }
  }
  
  simulationResult.value = result
}

export function addToHistory(entry) {
  simulationHistory.value.unshift(entry)
}

export function setDocuments(docs) {
  documents.value = docs
}
