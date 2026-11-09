"""esquema inicial: crea las 13 tablas de EPS VitalCare

Revision ID: 0001
Revises: 
Create Date: 2026-10-19 15:10:33.972895

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Generado con "alembic revision --autogenerate" y revisado manualmente.
    op.create_table('especialidades',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(length=80), nullable=False),
    sa.Column('descripcion', sa.String(length=255), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_especialidades')),
    sa.UniqueConstraint('nombre', name=op.f('uq_especialidades_nombre'))
    )
    op.create_table('usuarios',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('rol', sa.String(length=20), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(), nullable=False),
    sa.CheckConstraint("rol IN ('paciente', 'medico', 'admin')", name=op.f('ck_usuarios_rol_valido')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_usuarios'))
    )
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_usuarios_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_usuarios_rol'), ['rol'], unique=False)

    op.create_table('auditoria',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=True),
    sa.Column('accion', sa.String(length=50), nullable=False),
    sa.Column('recurso', sa.String(length=50), nullable=False),
    sa.Column('recurso_id', sa.Integer(), nullable=True),
    sa.Column('resultado', sa.String(length=20), nullable=False),
    sa.Column('detalle', sa.String(length=255), nullable=True),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name=op.f('fk_auditoria_usuario_id_usuarios'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_auditoria'))
    )
    with op.batch_alter_table('auditoria', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_auditoria_accion'), ['accion'], unique=False)
        batch_op.create_index(batch_op.f('ix_auditoria_creado_en'), ['creado_en'], unique=False)
        batch_op.create_index(batch_op.f('ix_auditoria_recurso'), ['recurso'], unique=False)
        batch_op.create_index(batch_op.f('ix_auditoria_usuario_id'), ['usuario_id'], unique=False)

    op.create_table('medicos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('nombres', sa.String(length=80), nullable=False),
    sa.Column('apellidos', sa.String(length=80), nullable=False),
    sa.Column('telefono', sa.String(length=20), nullable=False),
    sa.Column('registro_profesional', sa.String(length=30), nullable=False),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name=op.f('fk_medicos_usuario_id_usuarios'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_medicos')),
    sa.UniqueConstraint('registro_profesional', name=op.f('uq_medicos_registro_profesional')),
    sa.UniqueConstraint('usuario_id', name=op.f('uq_medicos_usuario_id'))
    )
    with op.batch_alter_table('medicos', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_medicos_apellidos'), ['apellidos'], unique=False)
        batch_op.create_index(batch_op.f('ix_medicos_nombres'), ['nombres'], unique=False)

    op.create_table('notificaciones',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('titulo', sa.String(length=120), nullable=False),
    sa.Column('mensaje', sa.String(length=500), nullable=False),
    sa.Column('tipo', sa.String(length=30), nullable=False),
    sa.Column('leida', sa.Boolean(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name=op.f('fk_notificaciones_usuario_id_usuarios'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_notificaciones'))
    )
    with op.batch_alter_table('notificaciones', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_notificaciones_usuario_id'), ['usuario_id'], unique=False)

    op.create_table('pacientes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('tipo_documento', sa.String(length=5), nullable=False),
    sa.Column('numero_documento', sa.String(length=20), nullable=False),
    sa.Column('nombres', sa.String(length=80), nullable=False),
    sa.Column('apellidos', sa.String(length=80), nullable=False),
    sa.Column('fecha_nacimiento', sa.Date(), nullable=False),
    sa.Column('telefono', sa.String(length=20), nullable=False),
    sa.Column('direccion', sa.String(length=150), nullable=True),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.CheckConstraint("tipo_documento IN ('CC', 'TI', 'CE', 'PA', 'RC')", name=op.f('ck_pacientes_tipo_documento_valido')),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name=op.f('fk_pacientes_usuario_id_usuarios'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_pacientes')),
    sa.UniqueConstraint('usuario_id', name=op.f('uq_pacientes_usuario_id'))
    )
    with op.batch_alter_table('pacientes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_pacientes_apellidos'), ['apellidos'], unique=False)
        batch_op.create_index(batch_op.f('ix_pacientes_nombres'), ['nombres'], unique=False)
        batch_op.create_index(batch_op.f('ix_pacientes_numero_documento'), ['numero_documento'], unique=True)

    op.create_table('servicios_medicos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('descripcion', sa.String(length=500), nullable=True),
    sa.Column('especialidad_id', sa.Integer(), nullable=False),
    sa.Column('duracion_minutos', sa.Integer(), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.CheckConstraint('duracion_minutos BETWEEN 10 AND 240', name=op.f('ck_servicios_medicos_duracion_valida')),
    sa.ForeignKeyConstraint(['especialidad_id'], ['especialidades.id'], name=op.f('fk_servicios_medicos_especialidad_id_especialidades'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_servicios_medicos')),
    sa.UniqueConstraint('nombre', name=op.f('uq_servicios_medicos_nombre'))
    )
    with op.batch_alter_table('servicios_medicos', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_servicios_medicos_especialidad_id'), ['especialidad_id'], unique=False)

    op.create_table('citas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('paciente_id', sa.Integer(), nullable=False),
    sa.Column('medico_id', sa.Integer(), nullable=False),
    sa.Column('servicio_id', sa.Integer(), nullable=False),
    sa.Column('fecha', sa.Date(), nullable=False),
    sa.Column('hora_inicio', sa.Time(), nullable=False),
    sa.Column('hora_fin', sa.Time(), nullable=False),
    sa.Column('motivo', sa.String(length=255), nullable=False),
    sa.Column('estado', sa.String(length=20), nullable=False),
    sa.Column('motivo_cancelacion', sa.String(length=255), nullable=True),
    sa.Column('cancelado_por_id', sa.Integer(), nullable=True),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(), nullable=False),
    sa.CheckConstraint("estado IN ('pendiente', 'confirmada', 'en_atencion', 'atendida', 'cancelada')", name=op.f('ck_citas_estado_valido')),
    sa.CheckConstraint('hora_fin > hora_inicio', name=op.f('ck_citas_rango_horas')),
    sa.ForeignKeyConstraint(['cancelado_por_id'], ['usuarios.id'], name=op.f('fk_citas_cancelado_por_id_usuarios'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['medico_id'], ['medicos.id'], name=op.f('fk_citas_medico_id_medicos'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id'], name=op.f('fk_citas_paciente_id_pacientes'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['servicio_id'], ['servicios_medicos.id'], name=op.f('fk_citas_servicio_id_servicios_medicos'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_citas'))
    )
    with op.batch_alter_table('citas', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_citas_estado'), ['estado'], unique=False)
        batch_op.create_index(batch_op.f('ix_citas_fecha'), ['fecha'], unique=False)
        batch_op.create_index('ix_citas_medico_fecha', ['medico_id', 'fecha'], unique=False)
        batch_op.create_index('ix_citas_paciente_fecha', ['paciente_id', 'fecha'], unique=False)
        batch_op.create_index(batch_op.f('ix_citas_servicio_id'), ['servicio_id'], unique=False)

    op.create_table('horarios_medicos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('medico_id', sa.Integer(), nullable=False),
    sa.Column('dia_semana', sa.Integer(), nullable=False),
    sa.Column('hora_inicio', sa.Time(), nullable=False),
    sa.Column('hora_fin', sa.Time(), nullable=False),
    sa.Column('duracion_cita_minutos', sa.Integer(), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.CheckConstraint('dia_semana BETWEEN 0 AND 6', name=op.f('ck_horarios_medicos_dia_valido')),
    sa.CheckConstraint('duracion_cita_minutos BETWEEN 10 AND 240', name=op.f('ck_horarios_medicos_duracion_valida')),
    sa.CheckConstraint('hora_fin > hora_inicio', name=op.f('ck_horarios_medicos_rango_horas')),
    sa.ForeignKeyConstraint(['medico_id'], ['medicos.id'], name=op.f('fk_horarios_medicos_medico_id_medicos'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_horarios_medicos'))
    )
    with op.batch_alter_table('horarios_medicos', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_horarios_medicos_medico_id'), ['medico_id'], unique=False)

    op.create_table('medico_especialidad',
    sa.Column('medico_id', sa.Integer(), nullable=False),
    sa.Column('especialidad_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['especialidad_id'], ['especialidades.id'], name=op.f('fk_medico_especialidad_especialidad_id_especialidades'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['medico_id'], ['medicos.id'], name=op.f('fk_medico_especialidad_medico_id_medicos'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('medico_id', 'especialidad_id', name=op.f('pk_medico_especialidad'))
    )
    op.create_table('solicitudes_autorizacion',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('paciente_id', sa.Integer(), nullable=False),
    sa.Column('servicio_id', sa.Integer(), nullable=False),
    sa.Column('motivo', sa.String(length=255), nullable=False),
    sa.Column('estado', sa.String(length=20), nullable=False),
    sa.Column('observaciones', sa.String(length=500), nullable=True),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(), nullable=False),
    sa.CheckConstraint("estado IN ('pendiente', 'en_revision', 'aprobada', 'rechazada')", name=op.f('ck_solicitudes_autorizacion_estado_valido')),
    sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id'], name=op.f('fk_solicitudes_autorizacion_paciente_id_pacientes'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['servicio_id'], ['servicios_medicos.id'], name=op.f('fk_solicitudes_autorizacion_servicio_id_servicios_medicos'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_solicitudes_autorizacion'))
    )
    with op.batch_alter_table('solicitudes_autorizacion', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_solicitudes_autorizacion_estado'), ['estado'], unique=False)
        batch_op.create_index(batch_op.f('ix_solicitudes_autorizacion_paciente_id'), ['paciente_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_solicitudes_autorizacion_servicio_id'), ['servicio_id'], unique=False)

    op.create_table('consultas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cita_id', sa.Integer(), nullable=False),
    sa.Column('resumen', sa.Text(), nullable=False),
    sa.Column('observaciones', sa.Text(), nullable=True),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['cita_id'], ['citas.id'], name=op.f('fk_consultas_cita_id_citas'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consultas')),
    sa.UniqueConstraint('cita_id', name=op.f('uq_consultas_cita_id'))
    )
    op.create_table('historial_autorizaciones',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('solicitud_id', sa.Integer(), nullable=False),
    sa.Column('estado_anterior', sa.String(length=20), nullable=True),
    sa.Column('estado_nuevo', sa.String(length=20), nullable=False),
    sa.Column('observacion', sa.String(length=500), nullable=True),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('creado_en', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['solicitud_id'], ['solicitudes_autorizacion.id'], name=op.f('fk_historial_autorizaciones_solicitud_id_solicitudes_autorizacion'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name=op.f('fk_historial_autorizaciones_usuario_id_usuarios'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_historial_autorizaciones'))
    )
    with op.batch_alter_table('historial_autorizaciones', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_historial_autorizaciones_solicitud_id'), ['solicitud_id'], unique=False)



def downgrade() -> None:
    # Generado con "alembic revision --autogenerate" y revisado manualmente.
    with op.batch_alter_table('historial_autorizaciones', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_historial_autorizaciones_solicitud_id'))

    op.drop_table('historial_autorizaciones')
    op.drop_table('consultas')
    with op.batch_alter_table('solicitudes_autorizacion', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_solicitudes_autorizacion_servicio_id'))
        batch_op.drop_index(batch_op.f('ix_solicitudes_autorizacion_paciente_id'))
        batch_op.drop_index(batch_op.f('ix_solicitudes_autorizacion_estado'))

    op.drop_table('solicitudes_autorizacion')
    op.drop_table('medico_especialidad')
    with op.batch_alter_table('horarios_medicos', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_horarios_medicos_medico_id'))

    op.drop_table('horarios_medicos')
    with op.batch_alter_table('citas', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_citas_servicio_id'))
        batch_op.drop_index('ix_citas_paciente_fecha')
        batch_op.drop_index('ix_citas_medico_fecha')
        batch_op.drop_index(batch_op.f('ix_citas_fecha'))
        batch_op.drop_index(batch_op.f('ix_citas_estado'))

    op.drop_table('citas')
    with op.batch_alter_table('servicios_medicos', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_servicios_medicos_especialidad_id'))

    op.drop_table('servicios_medicos')
    with op.batch_alter_table('pacientes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_pacientes_numero_documento'))
        batch_op.drop_index(batch_op.f('ix_pacientes_nombres'))
        batch_op.drop_index(batch_op.f('ix_pacientes_apellidos'))

    op.drop_table('pacientes')
    with op.batch_alter_table('notificaciones', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_notificaciones_usuario_id'))

    op.drop_table('notificaciones')
    with op.batch_alter_table('medicos', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_medicos_nombres'))
        batch_op.drop_index(batch_op.f('ix_medicos_apellidos'))

    op.drop_table('medicos')
    with op.batch_alter_table('auditoria', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_auditoria_usuario_id'))
        batch_op.drop_index(batch_op.f('ix_auditoria_recurso'))
        batch_op.drop_index(batch_op.f('ix_auditoria_creado_en'))
        batch_op.drop_index(batch_op.f('ix_auditoria_accion'))

    op.drop_table('auditoria')
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_usuarios_rol'))
        batch_op.drop_index(batch_op.f('ix_usuarios_email'))

    op.drop_table('usuarios')
    op.drop_table('especialidades')
