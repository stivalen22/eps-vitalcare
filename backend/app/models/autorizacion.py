from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ESTADOS_AUTORIZACION, sql_in
from app.core.timeutils import now_local
from app.db.base import Base


class SolicitudAutorizacion(Base):
    """Solicitud académica ficticia: sin validez administrativa, clínica ni legal."""

    __tablename__ = "solicitudes_autorizacion"
    __table_args__ = (
        CheckConstraint(f"estado IN ({sql_in(ESTADOS_AUTORIZACION)})", name="estado_valido"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="RESTRICT"), index=True)
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicios_medicos.id", ondelete="RESTRICT"), index=True)
    motivo: Mapped[str] = mapped_column(String(255))
    estado: Mapped[str] = mapped_column(String(20), index=True)
    observaciones: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)

    paciente: Mapped["Paciente"] = relationship(lazy="joined")  # noqa: F821
    servicio: Mapped["ServicioMedico"] = relationship(lazy="joined")  # noqa: F821
    historial: Mapped[list["HistorialAutorizacion"]] = relationship(
        back_populates="solicitud", order_by="HistorialAutorizacion.id", lazy="selectin"
    )

    @property
    def paciente_nombre(self) -> str:
        return self.paciente.nombre_completo

    @property
    def servicio_nombre(self) -> str:
        return self.servicio.nombre


class HistorialAutorizacion(Base):
    __tablename__ = "historial_autorizaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes_autorizacion.id", ondelete="RESTRICT"), index=True
    )
    estado_anterior: Mapped[str | None] = mapped_column(String(20), nullable=True)
    estado_nuevo: Mapped[str] = mapped_column(String(20))
    observacion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"))
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=now_local)

    solicitud: Mapped["SolicitudAutorizacion"] = relationship(back_populates="historial")
    usuario: Mapped["Usuario"] = relationship(lazy="joined")  # noqa: F821

    @property
    def usuario_nombre(self) -> str:
        return self.usuario.nombre_completo

    @property
    def usuario_rol(self) -> str:
        return self.usuario.rol
