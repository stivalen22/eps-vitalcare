from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import Usuario
from app.schemas.auth import ChangePasswordRequest, LoginRequest, ProfileUpdate, RegisterRequest, TokenResponse, UserMe
from app.schemas.common import Message
from app.services import auth_service
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Registro público de pacientes. Siempre asigna el rol paciente."""
    user = auth_service.register_patient(db, data)
    return TokenResponse(access_token=create_access_token(user.id, user.rol), user=UserMe.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    token, user = auth_service.login(db, data.email, data.password)
    return TokenResponse(access_token=token, user=UserMe.model_validate(user))


@router.get("/me", response_model=UserMe)
def me(user: Usuario = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserMe)
def update_me(data: ProfileUpdate, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Edita los campos permitidos del propio perfil (teléfono y dirección)."""
    return auth_service.update_profile(db, user, data)


@router.post("/change-password", response_model=Message)
def change_password(
    data: ChangePasswordRequest, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)
):
    auth_service.change_password(db, user, data)
    return Message(detail="Contraseña actualizada correctamente")
