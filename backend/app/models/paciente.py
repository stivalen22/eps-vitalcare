from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import TIPOS_DOCUMENTO, sql_in
from app.core.timeutils import now_local
from app.db.base import Base


class Paciente(Base):
    __tablename__ = "pacientes"
    __table_args__ = (
        CheckConstraint(f"tipo_documento IN ({sql_in(TIPOS_DOCUMENTO)})", name="tipo_documento_valido"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), unique=True)
    tipo_documento: Mapped[str] = mapped_column(String(5))
    numero_documento: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nombres: Mapped[str] = mapped_column(String(80), index=True)
    apellidos: Mapped[str] = mapped_column(String(80), index=True)
    fecha_nacimiento: Mapped[date] = mapped_column(Date)
    telefono: Mapped[str] = mapped_column(String(20))
    direccion: Mapped[str | None] = mapped_column(String(150), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=now_local)

    usuario: Mapped["Usuario"] = relationship(back_populates="paciente", lazy="joined")  # noqa: F821

    # Propiedades derivadas (no se duplican en la tabla)
    @property
    def email(self) -> str:
        return self.usuario.email

    @property
    def activo(self) -> bool:
        return self.usuario.activo

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"
