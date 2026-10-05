"""Generación de PDF (a pedido del cliente: las descargas son en PDF, nunca en
JSON). Dos usos:

- `build_answer_pdf`: la respuesta de una consulta — pregunta, respuesta final
  y bibliografía consultada. A propósito NO incluye la "receta": ni la
  trazabilidad del Loop 1, ni los prompts, ni las métricas internas.
- `build_document_pdf`: un documento generado (ej. un modelo de plan de cuentas
  o de estados financieros).

Usa fuentes estándar de PDF (Helvetica), que solo cubren Latin-1: alcanza para
el español (tildes, ñ, ¿ ¡). Lo que no esté en Latin-1 se reemplaza (ver
`_latin1`) en vez de romper la descarga.
"""
import io
import re
from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from app.config import settings

NAVY = (15, 23, 42)
GOLD = (153, 101, 21)
GRAY = (100, 116, 139)

_TYPOGRAPHY = {
    "‘": "'", "’": "'", "“": '"', "”": '"', "–": "-",
    "—": "-", "•": "-", "…": "...", " ": " ", "−": "-",
    "→": "->", "✓": "v", "✗": "x", "≤": "<=", "≥": ">=",
    "·": "-", " ": " ", "​": "",
}


def _latin1(text: str) -> str:
    for src, dst in _TYPOGRAPHY.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", "replace").decode("latin-1")


_LOGO_PATH = settings.BASE_DIR.parent / "frontend" / "public" / "iaas-logo.png"
_logo_cache: dict = {}


def _logo_bytes() -> bytes | None:
    """Escudo del simulador, reducido (el original pesa 1.6 MB y no hace falta
    en un encabezado de 9 mm)."""
    if "data" in _logo_cache:
        return _logo_cache["data"]
    data = None
    try:
        if Path(_LOGO_PATH).exists():
            from PIL import Image

            with Image.open(_LOGO_PATH) as im:
                im = im.convert("RGBA")
                im.thumbnail((140, 140))
                buf = io.BytesIO()
                im.save(buf, format="PNG", optimize=True)
                data = buf.getvalue()
    except Exception:
        data = None
    _logo_cache["data"] = data
    return data


class _BrandedPDF(FPDF):
    def __init__(self, doc_label: str):
        super().__init__(format="A4")
        self.doc_label = _latin1(doc_label)
        self.set_margins(18, 22, 18)
        self.set_auto_page_break(auto=True, margin=18)
        self.alias_nb_pages()

    def header(self):
        logo = _logo_bytes()
        if logo:
            self.image(io.BytesIO(logo), x=18, y=8, h=9)
        self.set_xy(30 if logo else 18, 9)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*NAVY)
        self.cell(0, 5, "Inglobals", new_x="LMARGIN", new_y="NEXT")
        self.set_x(30 if logo else 18)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 4, self.doc_label)
        self.set_draw_color(*GOLD)
        self.set_line_width(0.5)
        self.line(18, 19, self.w - 18, 19)
        self.set_y(23)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 5, f"inglobals.com/simulador  -  Página {self.page_no()} de {{nb}}", align="C")


def _heading(pdf: FPDF, text: str):
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*GOLD)
    pdf.cell(0, 5, _latin1(text.upper()), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*NAVY)
    pdf.ln(0.5)


def _paragraph(pdf: FPDF, text: str, size: float = 10.5, bold: bool = False, indent: float = 0):
    pdf.set_font("Helvetica", "B" if bold else "", size)
    pdf.set_text_color(30, 41, 59)
    pdf.set_x(pdf.l_margin + indent)
    pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - indent, size * 0.5 + 1.4, _latin1(text),
                   new_x="LMARGIN", new_y="NEXT")


def _fmt_date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso or ""


def build_answer_pdf(record: dict) -> bytes:
    """`record` es el resultado guardado de la consulta (result_json) más el
    texto original de la pregunta en `prompt`."""
    pdf = _BrandedPDF("Simulador Sostenible (IA) - Respuesta a la consulta")
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, 7, "Respuesta a la consulta", new_x="LMARGIN", new_y="NEXT")
    meta = " | ".join(x for x in [
        f"Expediente {record.get('expediente_id')}" if record.get("expediente_id") else "",
        _fmt_date(record.get("created_at", "")),
    ] if x)
    if meta:
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*GRAY)
        pdf.cell(0, 5, _latin1(meta), new_x="LMARGIN", new_y="NEXT")

    _heading(pdf, "Consulta")
    _paragraph(pdf, record.get("prompt") or record.get("refined_question") or "")
    refined = record.get("refined_question")
    if refined and refined != record.get("prompt"):
        _heading(pdf, "Pregunta interpretada")
        _paragraph(pdf, refined, size=10)

    loop2 = record.get("loop2") or {}
    _heading(pdf, "Respuesta")
    framework = record.get("framework")
    if framework:
        _paragraph(pdf, f"Marco normativo: {framework}", size=9, bold=True)
    for line in (loop2.get("final_answer") or "").splitlines() or [""]:
        _paragraph(pdf, line.strip() or " ")

    external = record.get("external") or {}
    if external.get("used") and external.get("claims"):
        _heading(pdf, "Complemento de búsqueda externa (no verificado en la bibliografía)")
        _paragraph(pdf, "La siguiente información proviene de una búsqueda externa con el modelo de IA y NO está "
                        "respaldada por la bibliografía documentada del simulador. Verifíquela antes de usarla.",
                   size=9)
        for claim in external["claims"]:
            _paragraph(pdf, f"- {claim}", size=10, indent=3)

    titles = []
    for src in record.get("sources_used") or []:
        t = src.get("title")
        if t and t not in titles and src.get("category") != "metodologica":
            titles.append(t)
    if titles:
        _heading(pdf, "Bibliografía consultada")
        for t in titles[:12]:
            _paragraph(pdf, f"- {t}", size=9, indent=3)

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GRAY)
    pdf.multi_cell(0, 4, _latin1(
        "Documento generado por el Simulador Sostenible (IA) de Inglobals con fines informativos. "
        "No sustituye el criterio profesional ni la consulta de la norma original."),
        new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


_ACCOUNT_RE = re.compile(r"^(\d+(?:\.\d+)*)\s+(.*)$")


def build_document_pdf(title: str, body: str, subtitle: str = "", doc_label: str = "Documento generado") -> bytes:
    """Documento de texto largo (modelo de plan de cuentas, de estados
    financieros...). Las líneas que empiezan con un código jerárquico
    ("1.1.2 Inventarios") se sangran según su profundidad; "#" marca títulos."""
    pdf = _BrandedPDF(f"Simulador Sostenible (IA) - {doc_label}")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*NAVY)
    pdf.multi_cell(0, 7, _latin1(title), new_x="LMARGIN", new_y="NEXT")
    if subtitle:
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*GRAY)
        pdf.multi_cell(0, 4.5, _latin1(subtitle), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    for raw in body.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        if not line.strip():
            pdf.ln(2)
            continue
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        if line.lstrip().startswith("#"):
            _heading(pdf, line.lstrip("# ").strip())
            continue
        m = _ACCOUNT_RE.match(line.strip())
        if m:
            depth = m.group(1).count(".")
            _paragraph(pdf, line.strip(), size=10 if depth <= 1 else 9.5, bold=depth <= 1, indent=min(depth, 4) * 5)
        else:
            lead = len(line) - len(line.lstrip())
            _paragraph(pdf, line.strip(), size=10, indent=min(lead, 12) * 0.8)

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GRAY)
    pdf.multi_cell(0, 4, _latin1(
        "Modelo de referencia generado con asistencia de IA a partir de la bibliografía del simulador. "
        "Revise y adapte a la entidad antes de usarlo; no sustituye el criterio profesional."),
        new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
