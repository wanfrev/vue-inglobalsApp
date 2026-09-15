from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.core.auth import (
    get_current_user,
    hash_password,
    validate_email,
    validate_password,
    verify_password,
)
from app.database import create_session, create_user, get_user_by_email
from app.models.schemas import AuthResponse, LoginRequest, RegisterRequest, UserStatus

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _to_auth_response(user: dict, token: str) -> AuthResponse:
    used = user["free_queries_used"]
    is_paid = bool(user["is_paid"])
    return AuthResponse(
        token=token,
        email=user["email"],
        free_queries_used=used,
        free_queries_remaining=0 if is_paid else max(0, settings.FREE_QUERY_LIMIT - used),
        is_paid=is_paid,
    )


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest):
    email = validate_email(payload.email)
    validate_password(payload.password)

    if get_user_by_email(email):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")

    user = create_user(email, hash_password(payload.password))
    token, _ = create_session(user["id"])
    return _to_auth_response(user, token)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    email = validate_email(payload.email)
    user = get_user_by_email(email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    token, _ = create_session(user["id"])
    return _to_auth_response(user, token)


@router.get("/me", response_model=UserStatus)
def me(user: dict = Depends(get_current_user)):
    used = user["free_queries_used"]
    is_paid = bool(user["is_paid"])
    return UserStatus(
        email=user["email"],
        free_queries_used=used,
        free_queries_remaining=0 if is_paid else max(0, settings.FREE_QUERY_LIMIT - used),
        is_paid=is_paid,
    )
