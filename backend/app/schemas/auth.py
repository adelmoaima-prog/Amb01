from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class MFAVerifyRequest(BaseModel):
    codigo: str
    temp_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    requires_mfa: bool = False
    temp_token: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    senha_atual: str
    senha_nova: str


class UserProfile(BaseModel):
    id: uuid.UUID
    nome: str
    email: str
    role: str
    totp_ativado: bool

    class Config:
        from_attributes = True
