from sqlalchemy import Column, Integer, Double, Numeric, Table, Text, String, DateTime, ForeignKey, Date, Boolean, TIMESTAMP
from sqlalchemy import Identity
from sqlalchemy.orm import relationship, declarative_base, backref
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import JSON

Base = declarative_base()

class Almacenamientos(Base):
    __tablename__ = "almacenamientos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True)
    capacidad = Column(Numeric(10, 2), nullable=False)
    poli_material = Column(Boolean, nullable=False)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)
    # Definición de relacion 1:M
    transacciones = relationship("Transacciones", backref="Almacenamientos")
    movimientos = relationship("Movimientos", backref="Almacenamientos")
    # Definicion de relación M:M
    materiales = relationship('Materiales', secondary='almacenamientos_materiales', back_populates='almacenamientos')

AlmacenamientosMateriales = Table("almacenamientos_materiales", Base.metadata,
    Column("almacenamiento_id", ForeignKey("almacenamientos.id"), primary_key=True),
    Column("material_id", ForeignKey("materiales.id"), primary_key=True),
    Column("saldo", Numeric(10,2), nullable=False),
    Column("fecha_hora", DateTime(timezone=True),  server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now())),
    Column("usuario_id", ForeignKey("usuarios.id"), primary_key=True),
)


class Bls(Base):
    __tablename__ = "bls"
    id = Column(Integer, primary_key=True, index=True)
    viaje_id = Column(Integer, ForeignKey("viajes.id"))
    material_id = Column(Integer, ForeignKey("materiales.id"))
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    no_bl = Column(String)
    peso_bl = Column(Numeric(10, 2))
    cargue_directo = Column(Boolean, nullable=False, default=0)
    estado_puerto = Column(Boolean, nullable=False, default=0)
    estado_operador = Column(Boolean, nullable=False, default=0)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)

    # Define relationships
    viaje = relationship("Viajes", backref=backref("bls"))
    material = relationship("Materiales", backref=backref("bls")) 

    __table_args__ = (
        UniqueConstraint('viaje_id', 'material_id', 'no_bl', name='uk_bls'),
    )

class Clientes(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    tipo_idetificacion = Column(String(10), nullable=False)
    num_identificacion = Column(Integer, nullable=False)
    razon_social = Column(String(100), nullable=False)
    primer_nombre = Column(String(30))
    segundo_nombre = Column(String(30))
    primer_apellido = Column(String(30))
    segundo_apellido = Column(String(30))
    id_actividad = Column(Integer)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)


class Flotas(Base):
    __tablename__ = "flotas"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(6))
    referencia = Column(String(300), unique=True, index=True)
    puntos = Column(Integer, nullable=True)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)
    estado_puerto = Column(Boolean)
    estado_operador = Column(Boolean)



class Viajes(Base):
    __tablename__ = "viajes"
    id = Column(Integer, primary_key=True, index=True)
    flota_id = Column(Integer,nullable=False)
    puerto_id = Column(String(300), unique=True, index=True)
    peso_meta = Column(Numeric(10,2), nullable=False, default=0)
    peso_real = Column(Numeric(10,2), nullable=True, default=0)
    fecha_llegada = Column(DateTime(timezone=True), nullable=True)
    fecha_salida = Column(DateTime(timezone=True), nullable=True)
    material_id = Column(Integer,nullable=True)
    viaje_origen = Column(String(300),nullable=True)
    despacho_directo = Column(Boolean, nullable=True)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)
    transacciones = relationship("Transacciones", backref="Viajes")



class Materiales(Base):
    __tablename__ = "materiales"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, index=True)
    codigo = Column(String(20), nullable=False)
    tipo = Column(String(50), nullable=False)
    densidad = Column(Numeric(4,2))
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)
    # Definición de relaciones 1:M
    transacciones = relationship("Transacciones", backref="Materiales")
    movimientos = relationship("Movimientos", backref="Materiales")
    # Definición de relaciones M:M
    almacenamientos = relationship('Almacenamientos', secondary='almacenamientos_materiales', back_populates='materiales')


    
class Roles(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    estado = Column(Boolean)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)
    usuarios = relationship("Usuarios", back_populates ="rol")
    permisos = relationship('Permisos', secondary='roles_permisos', back_populates='roles')


RolesPermisos = Table("roles_permisos", Base.metadata,
    Column("rol_id", ForeignKey("roles.id"), primary_key=True),
    Column("permiso_id", ForeignKey("permisos.id"), primary_key=True),
)

class Permisos(Base):
    __tablename__ = "permisos"
    id = Column(Integer, Identity(), primary_key=True, index=True)
    nombre = Column(String)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)
    roles = relationship("Roles", secondary="roles_permisos", back_populates="permisos")

class Usuarios(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, Identity(), primary_key=True, index=True)
    nick_name = Column(String(10), nullable=False, unique=True)
    full_name = Column(String(100), nullable=False)
    cedula = Column(Integer, nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    clave = Column(String(200), nullable=False)
    rol_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    rol = relationship("Roles", back_populates ="usuarios")
    recuperacion = Column(String(300), nullable=True)
    foto = Column(String, nullable=True)
    estado = Column(Boolean, nullable=False)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)

class Transacciones(Base):
    __tablename__ = "transacciones"
    id = Column(Integer, Identity(), primary_key=True, index=True)
    material_id = Column(Integer(), ForeignKey('materiales.id'), nullable=False)
    tipo = Column(String(50), nullable=False)
    viaje_id = Column(Integer(), ForeignKey('viajes.id'))
    pit = Column(Integer, nullable=True)
    ref1 = Column(String(50), nullable=True)
    ref2 = Column(String(50), nullable=True)
    fecha_inicio = Column(DateTime(timezone=True), nullable=True)
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
    origen_id = Column(Integer, ForeignKey('almacenamientos.id') ,nullable=True)
    destino_id = Column(Integer,nullable=True)
    peso_meta = Column(Numeric(10,2), nullable=False, default=0)
    peso_real = Column(Numeric(10,2), nullable=True)
    estado = Column(String(12), nullable=False)
    leido = Column(Boolean, nullable=False)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)
    bl_id = Column(Integer(), ForeignKey('bls.id'))
    movimientos = relationship("Movimientos", backref="Transacciones")
    pesadas = relationship("Pesadas", backref="Transacciones")

class Movimientos(Base):
    __tablename__ = "movimientos"
    id = Column(Integer, primary_key=True, index=True)
    transaccion_id = Column(Integer(), ForeignKey('transacciones.id'))
    almacenamiento_id = Column(Integer(), ForeignKey('almacenamientos.id'), nullable=False)
    material_id = Column(Integer(), ForeignKey('materiales.id'), nullable=False)
    tipo = Column(String(50), nullable=False)
    accion = Column(String(50), nullable=False)
    observacion = Column(String(50), nullable=True)
    peso = Column(Numeric(10,2), nullable=False)
    saldo_anterior = Column(Numeric(10,2), nullable=False)
    saldo_nuevo = Column(Numeric(10,2), nullable=True)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)

class Pesadas(Base):
    __tablename__ = "pesadas"
    id = Column(Integer, primary_key=True, index=True)
    transaccion_id = Column(Integer(), ForeignKey('transacciones.id'))
    consecutivo = Column(Double(), nullable=False)
    bascula_id = Column(Integer, nullable=True)
    peso_meta = Column(Numeric(10,2), nullable=True)
    peso_real = Column(Numeric(10,2), nullable=False)
    peso_vuelo = Column(Numeric(10,2), nullable=True)
    peso_fino = Column(Numeric(10,2), nullable=True)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)
    leido = Column(Boolean, nullable=False, default=False)


class PesadasCorte(Base):
    __tablename__ = "pesadas_corte"
    id = Column(Integer, primary_key=True, index=True)
    puerto_id = Column(String(50), nullable=True)
    transaccion = Column(Integer(), ForeignKey('transacciones.id'))
    consecutivo = Column(Double(), nullable=False)
    pit = Column(Integer, nullable=True)
    material = Column(String(50), nullable=True)
    peso = Column(Numeric(10,2), nullable=True)
    ref = Column(String(100), nullable=True)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)
    enviado = Column(Boolean, nullable=False, default=False)

class LogsAuditoria(Base):
    __tablename__ = 'logs_auditoria'
    id = Column(Integer, primary_key=True, index=True)
    entidad = Column(String, nullable=False)
    entidad_id = Column(Integer, nullable=False)
    accion = Column(String, nullable=False)
    valor_anterior = Column(JSON, nullable=True)
    valor_nuevo = Column(JSON, nullable=True)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)

class VBls(Base):
    __tablename__ = "v_bls"
    id = Column(Integer, primary_key=True, index=True)
    no_bl = Column(String, index=True)
    viaje_id = Column(Integer())
    viaje = Column(String)
    transaccion = Column(Integer(), nullable=True)
    referencia = Column(String(300), unique=True, nullable=True)
    material_id = Column(Integer)
    material = Column(String)
    cliente_id = Column(Integer)
    cliente = Column(String)
    peso_bl = Column(Numeric(10,2), nullable=False)
    peso_real = Column(Numeric(10,2), nullable=True)
    cargue_directo = Column(Boolean, nullable=True)
    estado_puerto = Column(Boolean, nullable=True)
    estado_operador = Column(Boolean, nullable=True)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)
    usuario = Column(String(200))

class VFlotas(Base):
    __tablename__ = "v_flotas"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(6))
    referencia = Column(String(300), unique=True, index=True)
    puntos = Column(Integer,nullable=True)
    estado_operador = Column(Boolean, nullable=True)
    estado_puerto = Column(Boolean, nullable=True)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)
    usuario = Column(String(200))


class VViajes(Base):
    __tablename__ = "v_viajes"
    id = Column(Integer, primary_key=True, index=True)
    flota_id = Column(Integer)
    referencia = Column(String)
    tipo = Column(String)
    puerto_id = Column(Integer)
    peso_meta = Column(Numeric(10,2), nullable=False)
    peso_real = Column(Numeric(10,2), nullable=False)
    fecha_llegada = Column(Date)
    fecha_salida = Column(Date)
    material_id = Column(Integer)
    material = Column(String)
    viaje_origen = Column(String)
    despacho_directo = Column(Boolean)
    estado_puerto = Column(Boolean, nullable=True)
    estado_operador = Column(Boolean, nullable=True)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)

class VPesadasAcumulado(Base):
    __tablename__ = "v_pesadas_acumulado"
    puerto_id = Column(String)
    referencia = Column(String)
    consecutivo = Column(Integer)
    transaccion = Column(Integer,  primary_key=True, index=True)
    pit = Column(Integer)
    material = Column(String)
    peso = Column(Numeric(10,2), nullable=False)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    usuario_id = Column(Integer, nullable=True)
    usuario = Column(String(200))


class VUsuariosRoles(Base):
    __tablename__ = "v_usuarios_roles"
    id = Column(Integer,  primary_key=True, index=True)
    nick_name = Column(String(10))
    full_name = Column(String(100))
    cedula = Column(Integer)
    email = Column(String(100))
    clave = Column(String(200))
    rol_id = Column(Integer)
    rol = Column(String(200))
    recuperacion = Column(String(300), nullable=True)
    foto = Column(String)
    estado = Column(Boolean)
    estado_rol = Column(Boolean)
    fecha_hora = Column(DateTime(timezone=True))
    usuario_id = Column(Integer, nullable=True)
    usuario = Column(String(200))

class VRolesPermisos(Base):
    __tablename__ = "v_roles_permisos"
    rol_id = Column(Integer)
    rol = Column(String(200))
    permiso_id = Column(Integer,  primary_key=True, index=True)
    permiso = Column(String(200))
    fecha_hora = Column(DateTime(timezone=True))
    usuario_id = Column(Integer, nullable=True)
    usuario = Column(String(200))


class VAlmMateriales(Base):
    __tablename__ = "v_almacenamientos_materiales"
    almacenamiento_id = Column(Integer, primary_key=True, index=True)
    almacenamiento = Column(String(200))
    material_id = Column(Integer)
    material = Column(String(200))
    saldo = Column(Numeric(10,2), nullable=False)
    fecha_hora = Column(DateTime(timezone=True))
    usuario_id = Column(Integer, nullable=True)
    usuario = Column(String(200))

class SaldoSnapshotScada(Base):
    __tablename__ = 'saldo_snapshot_scada'
    id = Column(Integer, primary_key=True, index=True)
    pesada_id = Column(Integer(), ForeignKey('pesadas.id'), nullable=False)
    # Ahora permitimos almacenamiento_id nullable para soportar snapshots que solo aplican a material
    almacenamiento_id = Column(Integer, nullable=True)
    material_id = Column(Integer, nullable=True)
    saldo_anterior = Column(Numeric(15,3), nullable=False)
    saldo_nuevo = Column(Numeric(15,3), nullable=False)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    # Tipo de snapshot: 'ORIGEN' o 'DESTINO' (para transacciones de traslado)
    tipo_almacenamiento = Column(String(10), nullable=True, default='ORIGEN')
    __table_args__ = (
        # Cambiada restricción: permite múltiples snapshots por pesada si son de diferentes almacenamientos
        UniqueConstraint('pesada_id', 'almacenamiento_id', name='uk_snapshot_pesada_alm'),
    )

class Ajustes(Base):
    __tablename__ = "ajustes"
    id = Column(Integer, primary_key=True, index=True)
    almacenamiento_id = Column(Integer, ForeignKey('almacenamientos.id'), nullable=False)
    material_id = Column(Integer, ForeignKey('materiales.id'), nullable=False)
    saldo_anterior = Column(Numeric(14,2), nullable=False)
    saldo_nuevo = Column(Numeric(14,2), nullable=False)
    delta = Column(Numeric(14,2), nullable=False)
    motivo = Column(String(255), nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    fecha_hora = Column(DateTime(timezone=True), server_default=func.timezone('America/Bogota', func.now()), onupdate=func.timezone('America/Bogota', func.now()))
    movimiento_id = Column(Integer, ForeignKey('movimientos.id'), nullable=True)

    # Relaciones opcionales
    movimiento = relationship('Movimientos', backref='ajustes')

### REPORTERIA

class Reporte(Base):
    """
    Modelo para el catálogo de reportes.
    Almacena la configuración y metadatos de cada reporte disponible.
    """
    __tablename__ = "reportes"

    # Identificación
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)

    # Configuración de vista
    vista_nombre = Column(String(100), nullable=False)
    campo_fecha = Column(String(50), default='fecha')

    # UI/UX
    icono = Column(String(50), default='assessment')
    orden = Column(Integer, default=0)
    color = Column(String(20), default='#1976d2')
    categoria = Column(String(50), default='operacional')

    # Configuración de exportación
    permite_exportar_pdf = Column(Boolean, default=True)
    permite_exportar_excel = Column(Boolean, default=True)
    permite_exportar_csv = Column(Boolean, default=True)

    # Configuración de filtros
    requiere_rango_fechas = Column(Boolean, default=True)
    permite_filtrar_material = Column(Boolean, default=True)

    # Estado
    activo = Column(Boolean, default=True)

    # Auditoría
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())
    fecha_actualizacion = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    usuario_creacion = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    usuario_actualizacion = Column(Integer, ForeignKey('usuarios.id'), nullable=True)

    # Relaciones
    columnas = relationship("ReporteColumna", back_populates="reporte", cascade="all, delete-orphan")
    permisos = relationship("PermisoReporte", back_populates="reporte")

    def __repr__(self):
        return f"<Reporte(codigo='{self.codigo}', nombre='{self.nombre}')>"

class ReporteColumna(Base):
    """
    Modelo para las columnas de cada reporte.
    Define la estructura y configuración de cada columna.
    """
    __tablename__ = "reportes_columnas"

    id = Column(Integer, primary_key=True, index=True)

    # Relación
    reporte_id = Column(Integer, ForeignKey('reportes.id', ondelete='CASCADE'), nullable=False)

    # Configuración de columna
    campo = Column(String(100), nullable=False)
    nombre_mostrar = Column(String(200), nullable=False)
    tipo_dato = Column(String(20), nullable=False)  # string, number, date, datetime, boolean

    # Opciones de visualización
    visible = Column(Boolean, default=True)
    orden = Column(Integer, default=0)
    ancho_minimo = Column(Integer, default=100)
    alineacion = Column(String(10), default='left')  # left, center, right

    # Opciones de interacción
    ordenable = Column(Boolean, default=True)
    filtrable = Column(Boolean, default=False)

    # Formato
    formato = Column(String(50), nullable=True)
    prefijo = Column(String(20), nullable=True)
    sufijo = Column(String(20), nullable=True)
    decimales = Column(Integer, default=2)

    # Totalizables
    es_totalizable = Column(Boolean, default=False)
    tipo_totalizacion = Column(String(20), nullable=True)  # sum, avg, count, min, max

    # Auditoría
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())

    # Relación
    reporte = relationship("Reporte", back_populates="columnas")

    # Restricciones
    __table_args__ = (
        UniqueConstraint('reporte_id', 'campo', name='uk_reporte_campo'),
    )

    def __repr__(self):
        return f"<ReporteColumna(reporte_id={self.reporte_id}, campo='{self.campo}')>"

class PermisoReporte(Base):
    """
    Modelo para permisos de reportes por rol.
    Controla quién puede ver y exportar cada reporte.
    """
    __tablename__ = "permisos_reportes"

    id = Column(Integer, primary_key=True, index=True)

    # Relaciones
    rol_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    codigo_reporte = Column(String(50), nullable=False)
    reporte_id = Column(Integer, ForeignKey('reportes.id'), nullable=True)

    # Permisos
    puede_ver = Column(Boolean, default=True)
    puede_exportar = Column(Boolean, default=True)

    # Auditoría
    fecha_hora = Column(TIMESTAMP, server_default=func.now())
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)

    # Relaciones
    reporte = relationship("Reporte", back_populates="permisos")

    # Restricciones
    __table_args__ = (
        UniqueConstraint('rol_id', 'codigo_reporte', name='uk_rol_reporte'),
    )

    def __repr__(self):
        return f"<PermisoReporte(rol_id={self.rol_id}, codigo='{self.codigo_reporte}')>"
