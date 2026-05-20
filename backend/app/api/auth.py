from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.core.security import (
    verify_password, create_access_token, create_refresh_token,
    decode_token, generate_totp_secret, get_totp_uri, verify_totp, get_password_hash
)
from app.schemas.auth import LoginRequest, MFAVerifyRequest, TokenResponse, UserProfile, ChangePasswordRequest
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.senha, user.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha inválidos")

    if not user.ativo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário inativo")

    await db.execute(
        update(User).where(User.id == user.id).values(ultimo_login=datetime.utcnow(), tentativas_login=0)
    )
    await db.commit()

    if user.totp_ativado and not settings.MFA_BYPASS_DEV:
        temp_token = create_access_token({"sub": str(user.id), "mfa_pending": True}, timedelta(minutes=5))
        return TokenResponse(requires_mfa=True, temp_token=temp_token)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token)


@router.post("/mfa/verify", response_model=TokenResponse)
async def verify_mfa(body: MFAVerifyRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.temp_token)
        user_id = payload.get("sub")
        mfa_pending = payload.get("mfa_pending")
        if not mfa_pending:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.totp_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")

    if not verify_totp(user.totp_secret, body.codigo):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Código MFA inválido")

    access_token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user)):
    await current_user.awaitable_attrs.role
    return UserProfile(
        id=current_user.id,
        nome=current_user.nome,
        email=current_user.email,
        role=current_user.role.nome,
        totp_ativado=current_user.totp_ativado,
    )


@router.get("/mfa/setup")
async def setup_mfa(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, current_user.email)
    await db.execute(update(User).where(User.id == current_user.id).values(totp_secret=secret))
    await db.commit()
    return {"secret": secret, "uri": uri}


@router.post("/mfa/activate")
async def activate_mfa(body: MFAVerifyRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Configure o MFA primeiro")
    if not verify_totp(current_user.totp_secret, body.codigo):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código inválido")
    await db.execute(update(User).where(User.id == current_user.id).values(totp_ativado=True))
    await db.commit()
    return {"mensagem": "MFA ativado com sucesso"}


@router.put("/me/senha")
async def change_password(body: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not verify_password(body.senha_atual, current_user.senha_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Senha atual incorreta")
    new_hash = get_password_hash(body.senha_nova)
    await db.execute(update(User).where(User.id == current_user.id).values(senha_hash=new_hash))
    await db.commit()
    return {"mensagem": "Senha alterada com sucesso"}
