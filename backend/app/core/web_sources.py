"""Consulta EN VIVO (en cada simulación, no pre-indexada) de un puñado de
sitios institucionales que el cliente pidió usar como fuente para el Prompt 2
(el validador), además de la bibliografía ya indexada en FAISS:

- SUNAI, SENIAT en línea y BCV: institucionales/fiscales de Venezuela.
- ONU Venezuela: marco de cooperación / ODS.
- OIE: normas internacionales del trabajo.

Se piden en paralelo con un timeout corto por sitio para no alargar la
respuesta del chat. Si un sitio falla o bloquea la petición (SENIAT e IOE
suelen rechazar tráfico automatizado sin un navegador real; BCV tiene un
certificado TLS con cadena incompleta), esa fuente simplemente se omite —
la simulación sigue con lo que sí se obtuvo más la bibliografía indexada,
nunca se corta por esto.

El contenido de estas páginas institucionales no cambia minuto a minuto, así
que se cachea en memoria (ver `_cache`) para no volver a pedirlas en cada
consulta — eso solo suma latencia y carga innecesaria a esos sitios. La
caché es por proceso (cada worker de Gunicorn tiene la suya), lo cual está
bien: sigue reduciendo drásticamente cuántas veces se golpea cada sitio.
"""
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

WEB_SOURCES = [
    {
        "url": "https://www.sunai.gob.ve/",
        "title": "SUNAI (Superintendencia Nacional de Auditoría Interna)",
        "category": "venezolana",
        "verify_ssl": True,
    },
    {
        "url": "https://seniatenlinea.seniat.gob.ve/documentacion-seniat-en-linea/",
        "title": "SENIAT en línea — Documentación",
        "category": "venezolana",
        "verify_ssl": True,
    },
    {
        "url": "https://www.bcv.org.ve/",
        "title": "Banco Central de Venezuela (BCV)",
        "category": "venezolana",
        # El certificado del BCV no valida la cadena completa en muchos
        # entornos; sin este flag la petición falla siempre con SSLError.
        "verify_ssl": False,
    },
    {
        "url": "https://venezuela.un.org/es",
        "title": "Naciones Unidas en Venezuela",
        "category": "venezolana",
        "verify_ssl": True,
    },
    {
        "url": "https://www.ioe-emp.org/es/prioridades-politicas/normas-internacionales-del-trabajo",
        "title": "OIE — Normas Internacionales del Trabajo",
        "category": "internacional",
        "verify_ssl": True,
    },
]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-VE,es;q=0.9",
}

MAX_CHARS_PER_SOURCE = 2500
FETCH_TIMEOUT_SECONDS = 4

# 20 min: en medio del rango de 15-30 min que se pidió. Si TODAS las fuentes
# fallaron (ej. un corte de red pasajero del VPS), no lo "congelamos" 20
# min — se reintenta pronto para no quedarnos sin nada más tiempo del
# necesario si la red se recupera antes.
CACHE_TTL_SECONDS = 20 * 60
EMPTY_CACHE_TTL_SECONDS = 60

_cache: dict = {"results": None, "fetched_at": 0.0}


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _fetch_one(source: dict) -> dict | None:
    try:
        response = requests.get(
            source["url"],
            headers=_HEADERS,
            timeout=FETCH_TIMEOUT_SECONDS,
            verify=source.get("verify_ssl", True),
        )
        response.raise_for_status()
    except requests.RequestException:
        return None

    text = _html_to_text(response.text)
    if not text:
        return None

    return {
        "title": source["title"],
        "category": source["category"],
        "text": text[:MAX_CHARS_PER_SOURCE],
        "score": 1.0,
        "url": source["url"],
    }


def _fetch_all_live() -> list[dict]:
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(WEB_SOURCES)) as pool:
        futures = [pool.submit(_fetch_one, source) for source in WEB_SOURCES]
        for future in as_completed(futures, timeout=FETCH_TIMEOUT_SECONDS + 3):
            try:
                result = future.result()
            except Exception:
                result = None
            if result:
                results.append(result)
    return results


def get_live_web_context() -> list[dict]:
    """Devuelve las fuentes vivas cacheadas si todavía valen (ver
    CACHE_TTL_SECONDS/EMPTY_CACHE_TTL_SECONDS); si no, las trae de nuevo en
    paralelo — solo las que respondieron a tiempo y con contenido. Nunca
    lanza excepción."""
    now = time.monotonic()
    cached = _cache["results"]
    if cached is not None:
        ttl = CACHE_TTL_SECONDS if cached else EMPTY_CACHE_TTL_SECONDS
        if (now - _cache["fetched_at"]) < ttl:
            return cached

    results = _fetch_all_live()
    _cache["results"] = results
    _cache["fetched_at"] = now
    return results
