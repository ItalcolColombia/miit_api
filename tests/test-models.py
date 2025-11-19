import asyncio
from typing import AsyncGenerator

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()  # Ensure this is the same Base instance

class Roles(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    estado = Column(Boolean)
    usuarios = relationship("Usuarios", back_populates="role")

class Usuarios(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, index=True)
    nick_name = Column(String(10), nullable=False, unique=True)
    full_name = Column(String(100), nullable=False)
    cedula = Column(Integer, nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    clave = Column(String(200), nullable=False)
    fecha_hora = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    rol_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    recuperacion = Column(String(300), nullable=True)
    foto = Column(String, nullable=True)
    estado = Column(Boolean, nullable=False)

    # Relationship to the Roles table
    role = relationship("Roles", back_populates="usuarios")

# Create the SQLAlchemy engine
engine = create_async_engine(
    "postgresql+asyncpg://postgres:M3t4l867s0ft@localhost:5432/PTOAntioquia_DW",
    echo=True,
    future=True,
)

# Create a session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency for retrieving a database session
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()




async def test_models():
    async for session in get_session():
        try:
            # Example: Fetch all roles
            query = select(Roles)
            result = await session.execute(query)
            roles = result.scalars().all()
            print("Roles:", roles)

            # Example: Fetch all users
            query = select(Usuarios)
            result = await session.execute(query)
            users = result.scalars().all()
            print("Users:", users)

        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_models())