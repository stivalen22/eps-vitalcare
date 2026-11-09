from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ROL_ADMIN, ROLES, sql_in
from app.core.timeutils import now_local
from app.db.base import Base


class Usuario(Base):
    """Cuenta de acceso. El perfil (paciente o médico) se guarda en su propia tabla."""

    __tablename__ = "usuarios"
    __table_args__ = (CheckConstraint(f"rol IN ({sql_in(ROLES)})", name="rol_valido"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(20), index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)

    paciente: Mapped["Paciente | None"] = relationship(back_populates="usuario", uselist=False, lazy="selectin")  # noqa: F821
    medico: Mapped["Medico | None"] = relationship(back_populates="usuario", uselist=False, lazy="selectin")  # noqa: F821

    @property
    def nombre_completo(self) -> str:
        if self.paciente:
            return f"{self.paciente.nombres} {self.paciente.apellidos}"
        if self.medico:
            return f"{self.medico.nombres} {self.medico.apellidos}"
        return "Administrador" if self.rol == ROL_ADMIN else self.email
