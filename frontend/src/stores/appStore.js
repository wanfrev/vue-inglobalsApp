import { ref } from 'vue'

export const currentView = ref('emulator')

export const simulationStatus = ref('idle')
export const promptText = ref('')

export function setView(view) {
  currentView.value = view
}
