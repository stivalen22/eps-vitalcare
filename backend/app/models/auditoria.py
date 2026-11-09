from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.timeutils import now_local
from app.db.base import Base


class Auditoria(Base):
    """Registro básico de acciones. No almacena contraseñas, tokens ni datos clínicos."""

    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    accion: Mapped[str] = mapped_column(String(50), index=True)
    recurso: Mapped[str] = mapped_column(String(50), index=True)
    recurso_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resultado: Mapped[str] = mapped_column(String(20), default="exito")
    detalle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=now_local, index=True)

    usuario: Mapped["Usuario | None"] = relationship(lazy="joined")  # noqa: F821

    @property
    def usuario_email(self) -> str | None:
        return self.usuario.email if self.usuario else None
