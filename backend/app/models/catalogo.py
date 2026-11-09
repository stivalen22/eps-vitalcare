from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.timeutils import now_local
from app.db.base import Base


class Especialidad(Base):
    __tablename__ = "especialidades"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=now_local)


class ServicioMedico(Base):
    """Servicio académico de ejemplo. No representa cobertura real de una EPS."""

    __tablename__ = "servicios_medicos"
    __table_args__ = (
        CheckConstraint("duracion_minutos BETWEEN 10 AND 240", name="duracion_valida"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    especialidad_id: Mapped[int] = mapped_column(ForeignKey("especialidades.id", ondelete="RESTRICT"), index=True)
    duracion_minutos: Mapped[int] = mapped_column(Integer)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=now_local)

    especialidad: Mapped["Especialidad"] = relationship(lazy="joined")

    @property
    def especialidad_nombre(self) -> str:
        return self.especialidad.nombre if self.especialidad else ""
