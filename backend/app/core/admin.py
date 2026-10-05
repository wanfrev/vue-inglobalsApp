import hmac

from fastapi import Header, HTTPException

from app.config import settings


def require_admin(x_admin_key: str | None = Header(None)) -> None:
    """Protege los endpoints que modifican la bibliografía (subir, borrar,
    adjuntar el archivo original). Si ADMIN_API_KEY no está definida en .env,
    no exige nada (comportamiento histórico); definida, hay que mandarla en el
    header X-Admin-Key."""
    if not settings.ADMIN_API_KEY:
        return
    if not hmac.compare_digest(x_admin_key or "", settings.ADMIN_API_KEY):
        raise HTTPException(status_code=401, detail="Se requiere la clave de administración.")
