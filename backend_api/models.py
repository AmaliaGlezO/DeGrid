from sqlalchemy import Column, String, Float, DateTime,Boolean,Integer
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

# 1. La base arquitectónica
Base = declarative_base()

class RegistroEnergetico(Base):
    __tablename__ = 'registro_energetico'

    fecha_hora = Column(DateTime(timezone=True), primary_key=True, index=True)
    circuito = Column(String, primary_key=True, index=True)
    temperatura_c = Column(Float, nullable=False)
    demanda_total_mw = Column(Float, nullable=False)
    generacion_solar_mw = Column(Float, nullable=False)
    generacion_termoelectrica_mw = Column(Float, nullable=False)
    generacion_bloques_flotantes_mw = Column(Float, nullable=False)
    temperatura_max_c = Column(Float, nullable=True)
    temperatura_min_c = Column(Float, nullable=True)

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    
    # El email será el identificador único para iniciar sesión
    email = Column(String(150), unique=True, index=True, nullable=False)
    
    # ⚠️ IMPORTANTE: Nunca guardamos la contraseña en texto plano, solo el hash seguro
    hashed_password = Column(String(255), nullable=False)
    
    # Almacenamos el rol como un string que coincida con nuestro Enum (UserRole)
    rol = Column(String(50), nullable=False)
    
    # Control operativo por si un usuario es suspendido o dado de baja
    activo = Column(Boolean, default=True)
    
    # Auditoría básica: fecha de creación del perfil
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Usuario {self.email} - Rol: {self.rol}>"