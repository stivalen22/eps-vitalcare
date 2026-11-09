from datetime import date, datetime, time

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ESTADOS_CITA, sql_in
from app.core.timeutils import now_local
from app.db.base import Base


class Cita(Base):
    __tablename__ = "citas"
    __table_args__ = (
        CheckConstraint(f"estado IN ({sql_in(ESTADOS_CITA)})", name="estado_valido"),
        CheckConstraint("hora_fin > hora_inicio", name="rango_horas"),
        Index("ix_citas_medico_fecha", "medico_id", "fecha"),
        Index("ix_citas_paciente_fecha", "paciente_id", "fecha"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="RESTRICT"))
    medico_id: Mapped[int] = mapped_column(ForeignKey("medicos.id", ondelete="RESTRICT"))
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicios_medicos.id", ondelete="RESTRICT"), index=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    hora_inicio: Mapped[time] = mapped_column(Time)
    hora_fin: Mapped[time] = mapped_column(Time)
    motivo: Mapped[str] = mapped_column(String(255))
    estado: Mapped[str] = mapped_column(String(20), index=True)
    motivo_cancelacion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cancelado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)

    paciente: Mapped["Paciente"] = relationship(lazy="joined")  # noqa: F821
    medico: Mapped["Medico"] = relationship(lazy="joined")  # noqa: F821
    servicio: Mapped["ServicioMedico"] = relationship(lazy="joined")  # noqa: F821
    consulta: Mapped["Consulta | None"] = relationship(back_populates="cita", uselist=False, lazy="selectin")

    @property
    def paciente_nombre(self) -> str:
        return self.paciente.nombre_completo

    @property
    def paciente_documento(self) -> str:
        return f"{self.paciente.tipo_documento} {self.paciente.numero_documento}"

    @property
    def medico_nombre(self) -> str:
        return self.medico.nombre_completo

    @property
    def servicio_nombre(self) -> str:
        return self.servicio.nombre

    @property
    def tiene_consulta(self) -> bool:
        return self.consulta is not None


class Consulta(Base):
    """Registro SIMULADO de una consulta. No contiene diagnósticos ni prescripciones reales."""

    __tablename__ = "consultas"

    id: Mapped[int] = mapped_column(primary_key=True)
    cita_id: Mapped[int] = mapped_column(ForeignKey("citas.id", ondelete="RESTRICT"), unique=True)
    resumen: Mapped[str] = mapped_column(Text)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=now_local)

    cita: Mapped["Cita"] = relationship(back_populates="consulta", lazy="joined")

    @property
    def fecha(self) -> date:
        return self.cita.fecha

    @property
    def paciente_id(self) -> int:
        return self.cita.paciente_id

    @property
    def medico_id(self) -> int:
        return self.cita.medico_id

    @property
    def paciente_nombre(self) -> str:
        return self.cita.paciente_nombre

    @property
    def medico_nombre(self) -> str:
        return self.cita.medico_nombre

    @property
    def servicio_nombre(self) -> str:
        return self.cita.servicio_nombre
