from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Proveedor de IA — cualquier endpoint compatible con el SDK de OpenAI
    # sirve (DeepSeek, Gemini vía su endpoint /v1beta/openai/, etc.). Cambiar
    # de proveedor es solo cambiar estas 3 variables en .env, no tocar código.
    AI_API_KEY: str = "sk_tu_clave_secreta_aqui"
    AI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    AI_MODEL: str = "gemini-3.6-flash"
    AI_TEMPERATURE: float = 0.1
    # Con modelos que "piensan" (ej. Gemini 3.6 Flash), el razonamiento interno
    # consume del mismo presupuesto de max_tokens que la respuesta visible.
    # 1000 corta la respuesta a la mitad (finish_reason="length", JSON
    # inválido) — verificado en pruebas reales. 4000 deja margen de sobra.
    AI_MAX_TOKENS: int = 4000

    # Precio por millón de tokens en USD. Verificar el valor vigente antes de
    # confiar en el costo estimado que se muestra al usuario — cambia con el
    # tiempo y según el proveedor/modelo. Para Gemini 3.6 Flash: verificado en
    # https://ai.google.dev/gemini-api/docs/pricing el 2026-09-12 ($0.75/$3.75
    # por 1M tokens hasta el 31-dic-2026, sube a $1.50/$7.50 desde ene-2027).
    AI_PRICE_INPUT_PER_1M: float = 0.75
    AI_PRICE_OUTPUT_PER_1M: float = 3.75

    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    # DATA_DIR es override-able con la variable de entorno DATA_DIR — en
    # Render (o cualquier host con disco persistente) debe apuntar a la ruta
    # del disco montado (ej. /var/data), no a una carpeta dentro del código
    # fuente, que se reconstruye en cada despliegue. CHROMA_DIR/UPLOADS_DIR/
    # SQLITE_DB se recalculan a partir de DATA_DIR en model_post_init, para
    # que sí seguían el override en vez de quedar fijos al valor por defecto.
    DATA_DIR: Path = BASE_DIR / "data"
    CHROMA_DIR: Path = Path("")
    UPLOADS_DIR: Path = Path("")
    SQLITE_DB: Path = Path("")

    # Dominios permitidos para llamar a esta API desde el navegador. En
    # desarrollo "*" es cómodo; en producción debe ser el dominio real de
    # Vercel (ej. "https://tu-app.vercel.app") — nunca dejar "*" en
    # producción si la API maneja sesiones/cookies. Se declara como texto
    # (no list[str]) a propósito: pydantic-settings intenta parsear los
    # campos list[str] desde la variable de entorno como JSON, y falla si le
    # pasas una lista separada por comas. Acepta uno o varios dominios
    # separados por comas; la lista real vive en CORS_ORIGINS_LIST.
    CORS_ORIGINS: str = "*"
    CORS_ORIGINS_LIST: list[str] = []

    # Freemium: cuántas consultas reales (no rechazadas por estar fuera de
    # contexto) puede procesar una sesión anónima antes de exigir pago.
    # Descargar la memoria técnica (/history/{id}/export) siempre requiere
    # ser cuenta paga, sin importar cuántas consultas le queden.
    FREE_QUERY_LIMIT: int = 2
    SESSION_EXPIRY_DAYS: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def model_post_init(self, __context) -> None:
        if not self.CHROMA_DIR.parts:
            self.CHROMA_DIR = self.DATA_DIR / "chroma"
        if not self.UPLOADS_DIR.parts:
            self.UPLOADS_DIR = self.DATA_DIR / "uploads"
        if not self.SQLITE_DB.parts:
            self.SQLITE_DB = self.DATA_DIR / "sqlite.db"
        self.CORS_ORIGINS_LIST = [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]


settings = Settings()

settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
