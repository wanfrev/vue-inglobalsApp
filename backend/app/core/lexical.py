"""Búsqueda léxica (BM25) sobre los fragmentos indexados.

Por qué existe: la búsqueda semántica usa all-MiniLM-L6-v2, un modelo
centrado en inglés. Con una bibliografía grande y en español, una consulta
como "retención de IVA de contribuyentes especiales" puede no traer la
providencia que lo regula (se vio en producción: estaba cargada y no
apareció). La coincidencia exacta de términos legales es justo lo que BM25
resuelve bien; se combina con la búsqueda semántica en rag.py.

Implementación con matrices dispersas de scipy (ya es dependencia de
sentence-transformers) para no multiplicar la memoria por worker.
"""
import re
import threading
import unicodedata

import numpy as np
from scipy import sparse

_STOPWORDS = frozenset(
    """de la el los las un una unos unas y o u e en a al del por para con sin sobre entre
    que se su sus lo le les es son ser esta este estos estas como mas pero si no ni
    ha han hay fue sera seran segun cada cual cuales quien quienes cuando donde porque
    debe deben puede pueden art articulo articulos presente ley parrafo numeral""".split()
)
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STEM_LEN = 7  # recorte simple: "retención"/"retenciones", "contribuyente"/"contribuyentes"

K1 = 1.5
B = 0.75

_lock = threading.Lock()
_cache: dict = {"key": None, "vocab": None, "weights": None}


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return [
        t[:_STEM_LEN]
        for t in _TOKEN_RE.findall(text)
        if len(t) >= 3 and t not in _STOPWORDS
    ]


def _build(metadata: list[dict]) -> None:
    vocab: dict[str, int] = {}
    rows, cols, vals = [], [], []
    doc_len = np.zeros(len(metadata), dtype=np.float32)
    for i, m in enumerate(metadata):
        counts: dict[int, int] = {}
        # El título cuenta: "Providencia ... Agentes de Retención del IVA" debe
        # ayudar a encontrar sus propios fragmentos aunque el texto no lo repita.
        for tok in tokenize(f"{m.get('title', '')} {m.get('text', '')}"):
            idx = vocab.setdefault(tok, len(vocab))
            counts[idx] = counts.get(idx, 0) + 1
        doc_len[i] = sum(counts.values())
        for idx, c in counts.items():
            rows.append(i)
            cols.append(idx)
            vals.append(c)

    n_docs, n_terms = len(metadata), len(vocab)
    tf = sparse.csr_matrix(
        (np.array(vals, dtype=np.float32), (np.array(rows), np.array(cols))),
        shape=(n_docs, n_terms),
    )
    df = np.bincount(tf.indices, minlength=n_terms).astype(np.float32)
    idf = np.log(1.0 + (n_docs - df + 0.5) / (df + 0.5)).astype(np.float32)
    avgdl = float(doc_len.mean()) if n_docs else 1.0

    # Pesos BM25 precalculados por (fragmento, término): score = pesos @ consulta.
    tf = tf.tocoo()
    norm = K1 * (1.0 - B + B * doc_len[tf.row] / max(avgdl, 1e-6))
    data = tf.data * (K1 + 1.0) / (tf.data + norm) * idf[tf.col]
    weights = sparse.csr_matrix((data.astype(np.float32), (tf.row, tf.col)), shape=(n_docs, n_terms))

    _cache.update(key=(id(metadata), n_docs), vocab=vocab, weights=weights)


def bm25_scores(metadata: list[dict], query: str) -> np.ndarray:
    """Puntaje BM25 de cada fragmento para la consulta (0 si no comparte
    ningún término). Reconstruye el índice léxico si los metadatos cambiaron."""
    n = len(metadata)
    if n == 0:
        return np.zeros(0, dtype=np.float32)
    key = (id(metadata), n)
    if _cache["key"] != key:
        with _lock:
            if _cache["key"] != key:
                _build(metadata)
    vocab, weights = _cache["vocab"], _cache["weights"]
    cols = sorted({vocab[t] for t in tokenize(query) if t in vocab})
    if not cols:
        return np.zeros(n, dtype=np.float32)
    q = np.zeros(weights.shape[1], dtype=np.float32)
    q[cols] = 1.0
    return np.asarray(weights @ q).ravel()
