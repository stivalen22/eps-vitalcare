from datetime import datetime, time

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DIAS_SEMANA
from app.core.timeutils import now_local
from app.db.base import Base


class HorarioMedico(Base):
    """Franja semanal de disponibilidad. dia_semana: 0=lunes ... 6=domingo."""

    __tablename__ = "horarios_medicos"
    __table_args__ = (
        CheckConstraint("dia_semana BETWEEN 0 AND 6", name="dia_valido"),
        CheckConstraint("hora_fin > hora_inicio", name="rango_horas"),
        CheckConstraint("duracion_cita_minutos BETWEEN 10 AND 240", name="duracion_valida"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    medico_id: Mapped[int] = mapped_column(ForeignKey("medicos.id", ondelete="RESTRICT"), index=True)
    dia_semana: Mapped[int] = mapped_column(Integer)
    hora_inicio: Mapped[time] = mapped_column(Time)
    hora_fin: Mapped[time] = mapped_column(Time)
    duracion_cita_minutos: Mapped[int] = mapped_column(Integer, default=30)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=now_local)

    medico: Mapped["Medico"] = relationship(lazy="joined")  # noqa: F821

    @property
    def medico_nombre(self) -> str:
        return self.medico.nombre_completo if self.medico else ""

    @property
    def dia_nombre(self) -> str:
        return DIAS_SEMANA[self.dia_semana]
