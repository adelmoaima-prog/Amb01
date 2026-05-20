from functools import wraps
from fastapi import HTTPException, status

ROLE_HIERARCHY = {
    "Admin": 4,
    "Coordenador": 3,
    "Medico": 2,
    "Recepcionista": 1,
}

ROLE_PERMISSIONS = {
    "Admin": ["*"],
    "Coordenador": [
        "dashboard:read",
        "agendas:read", "agendas:write",
        "escalas:read", "escalas:write",
        "absenteismo:read", "absenteismo:write",
        "producao:read",
        "capacidade:read", "capacidade:write",
        "relatorios:read", "relatorios:write",
        "profissionais:read",
        "especialidades:read",
        "consultorios:read",
        "users:read",
    ],
    "Medico": [
        "dashboard:read",
        "agendas:read",
        "escalas:read",
        "producao:read",
        "absenteismo:read",
    ],
    "Recepcionista": [
        "dashboard:read",
        "agendas:read",
        "consultas:read", "consultas:write",
        "absenteismo:read", "absenteismo:write",
    ],
}


def has_permission(role_name: str, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role_name, [])
    return "*" in perms or permission in perms


def require_roles(*roles: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if current_user is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
            user_role = current_user.role.nome if current_user.role else ""
            if user_role not in roles and "Admin" not in roles:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
