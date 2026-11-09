"""Dependencias de FastAPI: sesión de BD, usuario autenticado y control de roles."""
from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Usuario

bearer_scheme = HTTPBearer(auto_error=False, description="Pegue aquí el access_token obtenido en /auth/login")


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, message, headers={"WWW-Authenticate": "Bearer"})


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    if credentials is None:
        raise _unauthorized("No autenticado: se requiere un token de acceso")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _unauthorized("Token inválido o expirado") from None

    # El rol y el estado se leen SIEMPRE desde la base de datos, nunca desde el token o el navegador.
    user = db.get(Usuario, user_id)
    if user is None or not user.activo:
        raise _unauthorized("La sesión no es válida o la cuenta está desactivada")
    return user


def require_roles(*roles: str) -> Callable[..., Usuario]:
    def checker(user: Usuario = Depends(get_current_user)) -> Usuario:
        if user.rol not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene permisos para realizar esta operación")
        return user

    return checker


class Pagination:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Número de página"),
        size: int = Query(10, ge=1, le=100, description="Registros por página"),
    ):
        self.page = page
        self.size = size
