from pydantic_settings import BaseSettings
from cryptography.fernet import Fernet
from typing import Optional
import os


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ambuser:ambpass2024@localhost:5432/ambulatorio"
    SECRET_KEY: str = "supersecretkey-change-in-production-min32chars"
    FERNET_KEY: Optional[str] = None
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost"
    ENVIRONMENT: str = "development"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MFA_BYPASS_DEV: bool = True
    ALGORITHM: str = "HS256"
    REPORTS_DIR: str = "/app/reports"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def fernet(self) -> Fernet:
        key = self.FERNET_KEY or Fernet.generate_key()
        return Fernet(key if isinstance(key, bytes) else key.encode())

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
