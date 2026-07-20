import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Importamos tu modelo ya definido
from models import RegistroEnergetico


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# 1. Forzamos a la librería de PostgreSQL a usar codificación limpia
os.environ["PGCLIENTENCODING"] = "UTF8"

# 2. Imprimimos una ayuda visual para verificar qué ruta de BD está leyendo
print(f"👉 [DEBUG] Conectando a la BD: {os.getenv('DATABASE_URL')}")
# ------------------------------

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

try:
    print("🔍 Evaluando conexión en el arranque...")
    # Forzamos una conexión manual inmediata para capturar el fallo
    conexion_prueba = engine.raw_connection()
    conexion_prueba.close()
    print("✅ Conexión inicial exitosa.")
except UnicodeDecodeError as ude:
    print("\n❌ ¡Cazado! El mensaje oculto que PostgreSQL te estaba gritando es:")
    # ude.object guarda los bytes reales del choque. Los descodificamos en el formato de Windows
    mensaje_descifrado = ude.object.decode('cp1252', errors='replace')
    print(f"👉 {mensaje_descifrado}\n")
except Exception as e:
    print(f"\n❌ Fallo de conexión ordinario: {e}\n")
# Configuración básica de la base de datos


app = FastAPI(
    title="DeGrid API",
    description="API para la gestión y análisis de registros históricos de energía",
    version="1.0.0"
)

# Dependencia para abrir/cerrar la sesión de la BD en cada petición
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ENDPOINT 1: LISTAR CIRCUÍTOS ---
@app.get("/api/v1/circuitos", response_model=List[str])
def obtener_circuitos(db: Session = Depends(get_db)):
    """
    Retorna la lista única de todos los circuitos registrados (Ej. Habana_Vieja_1).
    """
    # Usamos distinct() para evitar duplicados en el millón de registros
    circuitos = db.query(RegistroEnergetico.circuito).distinct().all()
    
    # Al usar .all() con una sola columna, SQLAlchemy devuelve una lista de tuplas: [('Circuito1',), ('Circuito2',)]
    # Lo convertimos a una lista plana de strings
    return [c[0] for c in circuitos]


# --- ENDPOINT 2: MÉTRICAS OPTIMIZADAS (AGRUPADAS POR DÍA) ---
@app.get("/api/v1/energia/metricas")
def obtener_metricas(
    start_date: datetime = Query(..., description="Fecha de inicio (YYYY-MM-DD HH:MM:SS)"),
    end_date: datetime = Query(..., description="Fecha de fin (YYYY-MM-DD HH:MM:SS)"),
    circuito: Optional[str] = Query(None, description="Filtrar por un circuito específico"),
    db: Session = Depends(get_db)
):
    """
    Retorna el total de generación (solar vs termoeléctrica vs bloques flotantes) 
    y demanda, agrupado y optimizado por día para evitar congelar la API.
    """
    if start_date >= end_date:
        raise HTTPException(status_code=400, detail="La fecha de inicio debe ser anterior a la fecha de fin.")

    # 1. Definimos el truncamiento temporal (Agrupación analítica por DÍA)
    # date_trunc es una función nativa de PostgreSQL muy rápida
    unida_temporal = func.date_trunc('day', RegistroEnergetico.fecha_hora).label('dia')

    # 2. Construimos la consulta base con agregaciones analíticas (SUM)
    query = db.query(
        unida_temporal,
        func.sum(RegistroEnergetico.generacion_solar_mw).label('total_solar'),
        func.sum(RegistroEnergetico.generacion_termoelectrica_mw).label('total_termoelectrica'),
        func.sum(RegistroEnergetico.generacion_bloques_flotantes_mw).label('total_bloques_flotantes'),
        func.sum(RegistroEnergetico.demanda_total_mw).label('total_demanda')
    ).filter(
        RegistroEnergetico.fecha_hora >= start_date,
        RegistroEnergetico.fecha_hora <= end_date
    )

    # 3. Aplicamos filtro opcional si el usuario quiere un circuito específico
    if circuito:
        query = query.filter(RegistroEnergetico.circuito == circuito)

    # 4. Agrupamos y ordenamos por el día truncado
    resultados = query.group_by('dia').order_by('dia').all()

    # 5. Formateamos la respuesta final
    respuesta = []
    for fila in resultados:
        respuesta.append({
            "fecha": fila.dia.strftime("%Y-%m-%d"),
            "generacion_solar_mw_total": round(fila.total_solar, 2) if fila.total_solar else 0.0,
            "generacion_termoelectrica_mw_total": round(fila.total_termoelectrica, 2) if fila.total_termoelectrica else 0.0,
            "generacion_bloques_flotantes_mw_total": round(fila.total_bloques_flotantes, 2) if fila.total_bloques_flotantes else 0.0,
            "demanda_total_mw_total": round(fila.total_demanda, 2) if fila.total_demanda else 0.0
        })

    return {
        "rango_fechas": {"desde": start_date, "hasta": end_date},
        "registros_agrupados": len(respuesta),
        "datos": respuesta
    }