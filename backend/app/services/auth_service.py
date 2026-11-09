"""Registro, inicio de sesión y perfil."""
from sqlalchemy.orm import Session

from app.core.constants import ROL_MEDICO, ROL_PACIENTE
from app.core.errors import conflict
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Paciente, Usuario
from app.repositories import usuarios as repo
from app.schemas.auth import ChangePasswordRequest, ProfileUpdate, RegisterRequest
from app.services import audit_service, notification_service
from fastapi import HTTPException, status

INVALID_CREDENTIALS = "Correo o contraseña incorrectos"


def register_patient(db: Session, data: RegisterRequest) -> Usuario:
    if repo.email_exists(db, data.email):
        raise conflict("Ya existe una cuenta con ese correo electrónico")
    if repo.documento_exists(db, data.numero_documento):
        raise conflict("Ya existe un paciente con ese número de documento")

    user = Usuario(email=data.email, password_hash=hash_password(data.password), rol=ROL_PACIENTE, activo=True)
    db.add(user)
    db.flush()
    db.add(
        Paciente(
            usuario_id=user.id,
            tipo_documento=data.tipo_documento,
            numero_documento=data.numero_documento,
            nombres=data.nombres,
            apellidos=data.apellidos,
            fecha_nacimiento=data.fecha_nacimiento,
            telefono=data.telefono,
            direccion=data.direccion,
        )
    )
    notification_service.notify(
        db, user.id, "Bienvenido a EPS VitalCare", "Tu cuenta de paciente fue creada correctamente.", "cuenta"
    )
    audit_service.log(db, user.id, "registro", "usuario", user.id)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, email: str, password: str) -> tuple[str, Usuario]:
    user = repo.get_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        audit_service.log(db, user.id if user else None, "login", "sesion", resultado="fallido")
        db.commit()
        # Mismo mensaje para correo inexistente y contraseña errónea: no revela qué cuentas existen
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, INVALID_CREDENTIALS)
    if not user.activo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La cuenta está desactivada. Contacte al administrador.")
    audit_service.log(db, user.id, "login", "sesion")
    db.commit()
    return create_access_token(user.id, user.rol), user


def change_password(db: Session, user: Usuario, data: ChangePasswordRequest) -> None:
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La contraseña actual no es correcta")
    if data.current_password == data.new_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La nueva contraseña debe ser diferente a la actual")
    user.password_hash = hash_password(data.new_password)
    audit_service.log(db, user.id, "cambio_contrasena", "usuario", user.id)
    db.commit()


def update_profile(db: Session, user: Usuario, data: ProfileUpdate) -> Usuario:
    """El paciente puede editar teléfono y dirección; el médico, su teléfono."""
    fields = data.model_dump(exclude_unset=True)
    if user.rol == ROL_PACIENTE and user.paciente:
        if fields.get("telefono"):
            user.paciente.telefono = fields["telefono"]
        if "direccion" in fields:
            user.paciente.direccion = fields["direccion"]
    elif user.rol == ROL_MEDICO and user.medico:
        if fields.get("telefono"):
            user.medico.telefono = fields["telefono"]
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este tipo de cuenta no tiene campos de perfil editables")
    audit_service.log(db, user.id, "actualizar_perfil", "usuario", user.id)
    db.commit()
    db.refresh(user)
    return user
