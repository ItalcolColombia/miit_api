from sqlalchemy import Column, Integer, Double, Numeric, Table, String, DateTime, Boolean, ForeignKey, DECIMAL, \
    Date, Boolean, TIMESTAMP
from sqlalchemy import Identity
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declarative_base
from utils.any_utils import AnyUtils

Base = declarative_base()

class EmployeeModel(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    department = Column(String, nullable=False)
    salary = Column(DECIMAL(10, 2), nullable=False)
    birth_date = Column(Date, nullable=False)


class Almacenamientos(Base):
    __tablename__ = "almacenamientos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True)
    capacidad = Column(Numeric(10, 2), nullable=False)
    poli_material = Column(Boolean, nullable=False)
    # Definición de relacion 1:M
    transacciones = relationship("Transacciones", backref="Almacenamientos")
    movimientos = relationship("Movimientos", backref="Almacenamientos")
    # Definicion de relación M:M
    materiales = relationship('Materiales', secondary='almacenamientos_materiales', back_populates='almacenamientos')

AlmacenamientosMateriales = Table("almacenamientos_materiales", Base.metadata,
    Column("almacenamiento_id", ForeignKey("almacenamientos.id"), primary_key=True),
    Column("material_id", ForeignKey("materiales.id"), primary_key=True),
    Column("saldo", Numeric(10,2), nullable=False)
)

class Buques(Base):
    __tablename__ = "buques"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    estado = Column(Boolean)
    transacciones = relationship("Transacciones", backref="Buques")

class Camiones(Base):
    __tablename__ = "camiones"
    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(6), unique=True, index=True)
    puntos = Column(Integer, nullable=True)
    transacciones = relationship("Transacciones", backref="Camiones")


class Flotas(Base):
    __tablename__ = "flotas"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(6))
    referencia = Column(String(300), unique=True, index=True)
    consecutivo = Column(Double, nullable=False)
    peso = Column(Numeric(10,2), nullable=False)
    fecha_llegada = Column(DateTime(timezone=False), nullable=True)
    fecha_salida = Column(DateTime(timezone=False), nullable=True)
    material_id = Column(Integer,nullable=False)

class Materiales(Base):
    __tablename__ = "materiales"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, index=True)
    tipo = Column(String(50), nullable=False)
    densidad = Column(Numeric(4,2))
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
    usuarios = relationship("Usuarios", backref="Roles")
    permisos = relationship('Permisos', secondary='roles_permisos', back_populates='roles')


RolesPermisos = Table("roles_permisos", Base.metadata,
    Column("rol_id", ForeignKey("roles.id"), primary_key=True),
    Column("permiso_id", ForeignKey("permisos.id"), primary_key=True),
)

class Permisos(Base):
    __tablename__ = "permisos"
    id = Column(Integer, Identity(), primary_key=True, index=True)
    nombre = Column(String)
    roles = relationship("Roles", secondary="roles_permisos", back_populates="permisos"
)

class Usuarios(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, Identity(), primary_key=True, index=True)  # Auto-incrementing
    nick_name = Column(String(10), nullable=False, unique=True)
    full_name = Column(String(100), nullable=False)
    cedula = Column(Integer, nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    clave = Column(String(200), nullable=False)
    fecha_modificado = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    rol_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    recuperacion = Column(String(300), nullable=True)
    foto = Column(String, nullable=True)
    estado = Column(Boolean, nullable=False)

class Transacciones(Base):
    __tablename__ = "transacciones"
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer(), ForeignKey('materiales.id'), nullable=False)
    tipo = Column(String(50), nullable=False)
    ref1 = Column(String(50), nullable=True)
    ref2 = Column(String(50), nullable=True)
    fecha_creacion = Column(DateTime(timezone=False), nullable=True)
    fecha_inicio = Column(DateTime(timezone=False), nullable=True)
    fecha_fin = Column(DateTime(timezone=False), nullable=True)
    origen_id = Column(Integer, ForeignKey('almacenamientos.id') ,nullable=True)
    destino_id = Column(Integer,nullable=True)
    estado = Column(String(12), nullable=False)
    leido = Column(Boolean, nullable=False)
    buque_id = Column(Integer(), ForeignKey('buques.id'))
    camion_id = Column(Integer(), ForeignKey('camiones.id'))
    pit = Column(Integer, nullable=True)
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
    fecha_hora = Column(DateTime(timezone=False), nullable=False)
    peso = Column(Numeric(10,2), nullable=False)
    saldo_anterior = Column(Numeric(10,2), nullable=False)
    saldo_nuevo = Column(Numeric(10,2), nullable=True)

class Pesadas(Base):
    __tablename__ = "pesadas"
    id = Column(Integer, primary_key=True, index=True)
    transaccion_id = Column(Integer(), ForeignKey('transacciones.id'))
    consecutivo = Column(Double(), nullable=False)
    bascula_id = Column(Integer, nullable=True)
    fecha_hora = Column(DateTime(timezone=False), nullable=False)
    peso_meta = Column(Numeric(10,2), nullable=True)   
    peso_real = Column(Numeric(10,2), nullable=False)
    peso_vuelo = Column(Numeric(10,2), nullable=True)
    peso_fino = Column(Numeric(10,2), nullable=True)