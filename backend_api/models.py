from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.orm import declarative_base

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