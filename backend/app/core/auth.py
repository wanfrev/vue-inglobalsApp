"""Autenticación simple por correo + contraseña con token de sesión opaco
(no JWT: un token aleatorio guardado en la tabla `sessions`, más fácil de
revocar — basta con borrar la fila). Pensado para el registro rápido que
pidió el cliente, no para un sistema de identidad completo."""

import re

import bcrypt
from fastapi import Header, HTTPException

from app.database import get_user_by_token

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email: str) -> str:
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Correo inválido")
    return email


def validate_password(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(
            status_code=400, detail="La contraseña debe tener al menos 8 caracteres"
        )


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def get_current_user(authorization: str = Header(default="")) -> dict:
    """Dependency de FastAPI: exige `Authorization: Bearer <token>` y devuelve
    la fila de `users` asociada. 401 si falta, es inválido o expiró."""
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Falta el token de sesión")

    token = authorization[len("bearer "):].strip()
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada, inicia sesión de nuevo")
    return user
