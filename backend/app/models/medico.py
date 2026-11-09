from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.timeutils import now_local
from app.db.base import Base

# Tabla intermedia muchos a muchos: un médico puede tener varias especialidades
medico_especialidad = Table(
    "medico_especialidad",
    Base.metadata,
    Column("medico_id", ForeignKey("medicos.id", ondelete="CASCADE"), primary_key=True),
    Column("especialidad_id", ForeignKey("especialidades.id", ondelete="RESTRICT"), primary_key=True),
)


class Medico(Base):
    __tablename__ = "medicos"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), unique=True)
    nombres: Mapped[str] = mapped_column(String(80), index=True)
    apellidos: Mapped[str] = mapped_column(String(80), index=True)
    telefono: Mapped[str] = mapped_column(String(20))
    # Identificador académico ficticio, NO es un registro profesional real
    registro_profesional: Mapped[str] = mapped_column(String(30), unique=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=now_local)

    usuario: Mapped["Usuario"] = relationship(back_populates="medico", lazy="joined")  # noqa: F821
    especialidades: Mapped[list["Especialidad"]] = relationship(  # noqa: F821
        secondary=medico_especialidad, lazy="selectin", order_by="Especialidad.nombre"
    )

    @property
    def email(self) -> str:
        return self.usuario.email

    @property
    def activo(self) -> bool:
        return self.usuario.activo

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"
