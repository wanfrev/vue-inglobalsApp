// Formulario de Google del cliente: sirve tanto de buzón de sugerencias para
// temas no resueltos como de cuestionario general (se ofrece cada 3
// consultas de la sesión, ver SimulatorForm.vue).
export const FEEDBACK_FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLScaMVmgWRcQrd1Y05J9BcVYw3d4Rusiw0QGDrqXS7XXelZYyw/viewform?usp=header'

// El cuestionario aparece cada N consultas válidas de la sesión (3.ª, 6.ª,
// 9.ª...). No cuentan las preguntas fuera de alcance.
export const SURVEY_EVERY_N_QUERIES = 3

// Nombre del motor de búsqueda externa que se muestra al usuario (triangulación
// con el proveedor de IA configurado en el backend; hoy DeepSeek).
export const EXTERNAL_ENGINE_LABEL = 'DeepSeek'
