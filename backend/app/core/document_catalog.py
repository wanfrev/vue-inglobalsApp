"""Catálogo de referencia de las fuentes legales/normativas del Simulador DAD.

Este módulo documenta el corpus de documentos que vive en las carpetas de
Google Drive del proyecto y cómo deben clasificarse al subirlos con
``POST /api/v1/documents/upload`` (categorías válidas: ``venezolana``,
``internacional``, ``sostenibilidad`` — ver ``app.api.documents.VALID_CATEGORIES``).

No descarga ni indexa nada por sí mismo: es la guía que usa quien sube los
PDFs (o un futuro script de importación masiva) para no tener que adivinar
la categoría de cada archivo cada vez.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceEntry:
    file_name: str
    title: str
    category: str
    framework: str = ""  # norma/ley específica, si aplica (ej. "VEN-NIF 8", "NIA 230")


# Carpeta 1 — Sostenibilidad / RSE Banesco
_SOSTENIBILIDAD_BANESCO = [
    SourceEntry("CR11_114_A_002174_Banesco_1.pdf", "Expediente Banesco CR11-114-A-002174", "sostenibilidad"),
    SourceEntry("gri-guía-básica-para-tu-primer-reporte-de-sostenibilidad.pdf", "Guía básica GRI para tu primer reporte de sostenibilidad", "sostenibilidad", "GRI"),
    SourceEntry("Guía-para-pymes-ante-los-ODS.pdf", "Guía para PyMEs ante los ODS", "sostenibilidad", "ODS"),
    SourceEntry("Informe deSostenibilidad.pdf", "Informe de Sostenibilidad", "sostenibilidad"),
    SourceEntry("informe-pacto-global-banesco-2012_banesco.pdf", "Informe Pacto Global Banesco 2012", "sostenibilidad", "Pacto Global"),
    SourceEntry("informe-pacto-global-banesco-2013_banesco_pacto_social.pdf", "Informe Pacto Global Banesco 2013 — Pacto Social", "sostenibilidad", "Pacto Global"),
    SourceEntry("informe-responsabilidad-social-2023-espanol_banesco.pdf", "Informe de Responsabilidad Social 2023 Banesco", "sostenibilidad"),
    SourceEntry("informe-rse-y-sostenibilidad-2024_Banesco.pdf", "Informe RSE y Sostenibilidad 2024 Banesco", "sostenibilidad"),
    SourceEntry("ISSB.pdf", "ISSB — Normas Internacionales de Sostenibilidad", "sostenibilidad", "ISSB / NIIF S1-S2"),
    SourceEntry("Los-Diez-Principios-del-Pacto-Mundial.pdf", "Los Diez Principios del Pacto Mundial", "sostenibilidad", "Pacto Global"),
    SourceEntry("Master Class Unidad 5.pdf", "Master Class — Unidad 5", "sostenibilidad"),
    SourceEntry("Master Class.pdf", "Master Class de Sostenibilidad", "sostenibilidad"),
    SourceEntry("VENNS0V0.pdf", "VEN-NS 0 — Norma Venezolana de Sostenibilidad", "sostenibilidad", "VEN-NS 0"),
]

# Carpeta 2 — Curso RS
_CURSO_RS = [
    SourceEntry("Curso RS tema 2-1.pdf", "Curso de Responsabilidad Social — Tema 2 (parte 1)", "sostenibilidad"),
    SourceEntry("Curso RS tema 2.pdf", "Curso de Responsabilidad Social — Tema 2", "sostenibilidad"),
]

# Carpeta 3 — vacía al momento de este catálogo (sin archivos públicos)

# Carpeta 4 — Reglamento de IA de la Unión Europea
_AI_ACT_UE = [
    SourceEntry("IA_UNION_EUROPEA_ESPANOL_L00001-00144.pdf", "Reglamento de IA de la Unión Europea (español)", "internacional", "EU AI Act"),
    SourceEntry("IA_Union_Europea_OJ_L_202401689_EN_TXT.pdf", "EU AI Act — Official Journal text (English)", "internacional", "EU AI Act"),
]

# Carpeta 5 — Ética profesional y normas contables internacionales
_ETICA_Y_NORMAS = [
    SourceEntry("2023-Manual-2023-IESBA, Código de Etica Spanish LOCKED.pdf", "Código de Ética IESBA 2023 (español)", "internacional", "IESBA"),
    SourceEntry("GuiaIA-Traduccion2706.pdf", "Guía de IA (traducción)", "internacional"),
    SourceEntry("Norma de Contabilidad NIIF para las PYME edición 2015 .pdf", "NIIF para las PYMES — edición 2015", "internacional", "NIIF PYME"),
    SourceEntry("Norma Internacional de Educacion 2019.pdf", "Norma Internacional de Educación 2019", "internacional", "IES"),
]

# Carpeta 6 — Auditoría (NIAS/ISA)
_AUDITORIA_NIAS = [
    SourceEntry("AUDITORIA UN ENFOQUE INTEGRAL.pdf", "Auditoría: un enfoque integral (libro de texto)", "internacional"),
    SourceEntry("ISAE-3410.pdf", "ISAE 3410 — Encargos de aseguramiento sobre gases de efecto invernadero", "internacional", "ISAE 3410"),
    SourceEntry("Manual de NIAS edición 2021 Volumen 3.pdf", "Manual de NIAS 2021 — Volumen III", "internacional", "NIA"),
    SourceEntry("Manual de NIAS edición 2021 Volumen I.pdf", "Manual de NIAS 2021 — Volumen I", "internacional", "NIA"),
    SourceEntry("Manual de NIAS edición 2021 Volumen II.pdf", "Manual de NIAS 2021 — Volumen II", "internacional", "NIA"),
    SourceEntry("NIA para EMC .pdf", "NIA para Entidades de Menor Complejidad (EMC)", "internacional", "NIA"),
    SourceEntry("NIAE 5000.pdf", "NIAE 5000", "internacional", "NIAE 5000"),
    SourceEntry("Normas Globales de Auditoria Interna.pdf", "Normas Globales de Auditoría Interna", "internacional"),
    SourceEntry("Papeles_de_Trabajo_ANEXOS_Auditoria_financiera_CARLOS_ALBERTO_MONTES.pdf", "Ejemplo de papeles de trabajo — auditoría financiera", "internacional"),
]

# Carpeta 7 — Leyes venezolanas de tecnología, datos e IA
_LEYES_VE_TECNOLOGIA = [
    SourceEntry("Codigo_de_Etica_de_Inteligencia_Artificial_de_la_Republica_Bolivariana-1.pdf", "Código de Ética de Inteligencia Artificial de la República Bolivariana de Venezuela", "venezolana"),
    SourceEntry("GuiaIA-Traduccion2706.pdf", "Guía de IA (traducción)", "venezolana"),
    SourceEntry("ley_archivo_digital.pdf", "Ley de Archivo Digital", "venezolana"),
    SourceEntry("Ley_datos_mensajes.pdf", "Ley de Mensajes de Datos y Firmas Electrónicas", "venezolana"),
    SourceEntry("Ley_mensaje_datos_venezuela.pdf", "Ley de Mensajes de Datos (Venezuela)", "venezolana"),
    SourceEntry("ley_propiedad_intelectual.pdf", "Ley de Propiedad Intelectual", "venezolana"),
    SourceEntry("ley-de-infogobierno-20211108160540_auditoria_de_estado.pdf", "Ley de Infogobierno", "venezolana"),
    SourceEntry("ley-especial_ilicito_electronico_fraude.pdf", "Ley Especial contra los Delitos Informáticos", "venezolana"),
    SourceEntry("ley-organica_contra_la_delincuencia_financiera.pdf", "Ley Orgánica contra la Delincuencia Financiera", "venezolana"),
]

# Carpeta 8 — Leyes y normas contables venezolanas (VEN-NIF)
_LEYES_VE_CONTABLES = [
    SourceEntry("2.SECP-3 Compatibilidad de Ejercicio Simultáneo de la Función de Comisario y Auditor Externo. .pdf", "SECP-3 — Compatibilidad Comisario / Auditor Externo", "venezolana", "SECP-3"),
    SourceEntry("1973_Ley_de_Ejercicio.pdf", "Ley de Ejercicio de la Contaduría Pública (1973)", "venezolana"),
    SourceEntry("20170330_BA_VEN-NIF_Nro_8_V-4.pdf", "BA VEN-NIF N° 8 — versión 4", "venezolana", "VEN-NIF 8"),
    SourceEntry("BA VEN NIF 0 VERSION 6.pdf", "BA VEN-NIF N° 0 — versión 6", "venezolana", "VEN-NIF 0"),
    SourceEntry("BA VEN-NIF N 2 Version 4-1.pdf", "BA VEN-NIF N° 2 — versión 4", "venezolana", "VEN-NIF 2"),
    SourceEntry("BA VEN-NIF N 4 Version 1.pdf", "BA VEN-NIF N° 4 — versión 1", "venezolana", "VEN-NIF 4"),
    SourceEntry("BA VEN-NIF N 11 Version 0.pdf", "BA VEN-NIF N° 11 — versión 0", "venezolana", "VEN-NIF 11"),
    SourceEntry("BA VEN-NIF N 12 version 0.pdf", "BA VEN-NIF N° 12 — versión 0", "venezolana", "VEN-NIF 12"),
    SourceEntry("BA VEN-NIF N° 8 VERSIÓN N° 10 “PRINCIPIOS DE CONTABILIDAD GENERALMENTE ACEPTADOS EN VENEZUELA (VEN-N.pdf", "BA VEN-NIF N° 8 — versión 10 (PCGA Venezuela)", "venezolana", "VEN-NIF 8"),
    SourceEntry("BA VEN-NIF Nº 5 Version 3-1.pdf", "BA VEN-NIF N° 5 — versión 3", "venezolana", "VEN-NIF 5"),
    SourceEntry("BA VEN-NIF Nº 5 Version 3.pdf", "BA VEN-NIF N° 5 — versión 3", "venezolana", "VEN-NIF 5"),
    SourceEntry("BA VEN-NIF Nº 9 .pdf", "BA VEN-NIF N° 9", "venezolana", "VEN-NIF 9"),
    SourceEntry("codigo civil d eveenzuela.pdf", "Código Civil de Venezuela", "venezolana"),
    SourceEntry("Codigo-de-Comercio.pdf", "Código de Comercio", "venezolana"),
    SourceEntry("codigo-organico-tributario.pdf", "Código Orgánico Tributario", "venezolana"),
    SourceEntry("constitucion-nacional-20191205135853.PDF", "Constitución de la República Bolivariana de Venezuela", "venezolana"),
    SourceEntry("Ley contraloria sobre papeles de trabajo.pdf", "Ley de Contraloría — papeles de trabajo", "venezolana"),
    SourceEntry("LEY ORGÁNICA DE LA CONTRALORÍA GENERAL DE LA REPÚBLICA.pdf", "Ley Orgánica de la Contraloría General de la República", "venezolana"),
    SourceEntry("ley-de-archivos-nacionales-20220822125032.pdf", "Ley de Archivos Nacionales", "venezolana"),
    SourceEntry("Resolución 90 del Directorio de la FCCPV 2024 .pdf", "Resolución N° 90 del Directorio de la FCCPV (2024)", "venezolana"),
    SourceEntry("SECP 6 Normas Interprofesionales para el ejercicio de la función de Comisario .pdf", "SECP 6 — Normas Interprofesionales del Comisario", "venezolana", "SECP-6"),
    SourceEntry("SECP 8.pdf", "SECP 8", "venezolana", "SECP-8"),
    SourceEntry("SECP-3 .pdf", "SECP-3", "venezolana", "SECP-3"),
    SourceEntry("SEP-7.pdf", "SEP-7", "venezolana", "SEP-7"),
]

DOCUMENT_CATALOG: list[SourceEntry] = [
    *_SOSTENIBILIDAD_BANESCO,
    *_CURSO_RS,
    *_AI_ACT_UE,
    *_ETICA_Y_NORMAS,
    *_AUDITORIA_NIAS,
    *_LEYES_VE_TECNOLOGIA,
    *_LEYES_VE_CONTABLES,
]

_BY_FILE_NAME = {entry.file_name.lower(): entry for entry in DOCUMENT_CATALOG}


def lookup_by_file_name(file_name: str) -> SourceEntry | None:
    """Busca la entrada del catálogo por nombre exacto de archivo (case-insensitive)."""
    return _BY_FILE_NAME.get(file_name.lower())


def suggest_category(file_name: str) -> str | None:
    """Devuelve la categoría sugerida para un archivo, por coincidencia exacta de
    nombre en el catálogo o, si no hay match, por palabras clave en el nombre.
    Devuelve None si no puede sugerir nada con confianza (mejor pedirle al usuario
    que elija la categoría manualmente antes que adivinar mal)."""
    exact = lookup_by_file_name(file_name)
    if exact:
        return exact.category

    lowered = file_name.lower()
    venezuela_keywords = ("ven-nif", "venezolana", "venezuela", "gaceta", "secp", "seniat", "contraloria", "contraloría", "codigo civil", "código civil", "codigo de comercio", "código de comercio", "constitucion", "constitución")
    sostenibilidad_keywords = ("sostenibilidad", "ods", "gri", "issb", "pacto-global", "pacto_global", "responsabilidad-social", "responsabilidad_social", "ven-ns", "venns")
    internacional_keywords = ("nia", "niif", "isae", "iesba", "ai_act", "ai-act", "union_europea", "unión europea", "ies ")

    if any(k in lowered for k in venezuela_keywords):
        return "venezolana"
    if any(k in lowered for k in sostenibilidad_keywords):
        return "sostenibilidad"
    if any(k in lowered for k in internacional_keywords):
        return "internacional"
    return None
