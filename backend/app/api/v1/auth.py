from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user_id, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
)
from app.schemas.user import (
    ForgotPasswordRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import blacklist_token, is_token_blacklisted
from app.services.user_service import UserService
from app.workers.tasks.emails import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])

# Resposta uniforme do forgot-password — idêntica exista ou não o e-mail,
# para não vazar quais e-mails estão cadastrados.
_FORGOT_PASSWORD_MESSAGE = (
    "Se o e-mail estiver cadastrado, enviaremos um link de recuperação."
)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    data: UserCreate, db: AsyncSession = Depends(get_db)
) -> UserResponse:
    svc = UserService(db)
    if await svc.email_exists(data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado",
        )
    user = await svc.create(data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    svc = UserService(db)
    user = await svc.authenticate(data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token inválido ou expirado",
    )
    if await is_token_blacklisted(data.refresh_token):
        raise credentials_exception
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise credentials_exception
        user_id = int(payload["sub"])
    except Exception:
        raise credentials_exception from None

    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user:
        raise credentials_exception

    # Invalida o refresh token anterior
    await blacklist_token(data.refresh_token)

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: RefreshRequest,
    _user_id: int = Depends(get_current_user_id),
) -> None:
    await blacklist_token(data.refresh_token)


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    svc = UserService(db)
    user = await svc.get_by_email(data.email)
    if user:
        token = create_reset_token(user.id)
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        # Fire-and-forget via Celery: o handler retorna imediatamente nos dois
        # casos (e-mail existente ou não), sem esperar o envio SMTP.
        send_password_reset_email.delay(user.email, reset_link)
    return {"message": _FORGOT_PASSWORD_MESSAGE}


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    invalid_token = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Token inválido ou expirado",
    )
    if await is_token_blacklisted(data.token):
        raise invalid_token
    try:
        payload = decode_token(data.token)
    except Exception:
        raise invalid_token from None
    if payload.get("type") != "reset":
        raise invalid_token
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise invalid_token from None

    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user:
        raise invalid_token

    await svc.update_password(user, data.new_password)
    # Single-use: invalida o token de reset após o uso bem-sucedido.
    await blacklist_token(data.token)

    return {"message": "Senha alterada com sucesso."}


@router.get("/me", response_model=UserResponse)
async def me(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado"
        )
    return UserResponse.model_validate(user)
