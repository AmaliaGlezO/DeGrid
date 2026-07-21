import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from models import RegistroEnergetico
from enum import Enum
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from auth import obtener_password_hash, verificar_password, crear_token_acceso
from models import Usuario 
from sqlalchemy import extract, case

class UserRole(str, Enum):
    DESPACHADOR = "Despachador de Carga"
    DIRECTOR = "Director Provincial"
    INSPECTOR = "Inspector de Eficiencia"


class UserRegister(BaseModel):
    nombre: str
    email: str
    password: str
    rol: UserRole 

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

    class Config:
        from_attributes = True

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

os.environ["PGCLIENTENCODING"] = "UTF8"

print(f"👉 [DEBUG] Conectando a la BD: {os.getenv('DATABASE_URL')}")


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

try:
    print("🔍 Evaluando conexión en el arranque...")
    # Forzamos una conexión manual inmediata para capturar el fallo
    conexion_prueba = engine.raw_connection()
    conexion_prueba.close()
    print(" Conexión inicial exitosa.")
except UnicodeDecodeError as ude:
    print("\n ¡Cazado! El mensaje oculto que PostgreSQL te estaba gritando es:")
    # ude.object guarda los bytes reales del choque. Los descodificamos en el formato de Windows
    mensaje_descifrado = ude.object.decode('cp1252', errors='replace')
    print(f" {mensaje_descifrado}\n")
except Exception as e:
    print(f"\n Fallo de conexión ordinario: {e}\n")


app = FastAPI(
    title="DeGrid API",
    description="API para la gestión y análisis de registros históricos de energía",
    version="1.0.0"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/v1/circuitos", response_model=List[str])
def obtener_circuitos(db: Session = Depends(get_db)):
    """
    Retorna la lista única de todos los circuitos registrados.
    """

    circuitos = db.query(RegistroEnergetico.circuito).distinct().all()
    

    return [c[0] for c in circuitos]


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

    unida_temporal = func.date_trunc('day', RegistroEnergetico.fecha_hora).label('dia')

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

    if circuito:
        query = query.filter(RegistroEnergetico.circuito == circuito)

    resultados = query.group_by('dia').order_by('dia').all()

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



@app.get("/api/v1/analitica/picos-demanda")
def obtener_picos_demanda(db: Session = Depends(get_db)):
    """
    Analiza todo el histórico para determinar la demanda máxima registrada (MW)
    agrupada por año, dividida en dos bandas horarias críticas:
    - Pico Diurno (11:00 - 13:59)
    - Pico Nocturno (18:00 - 22:59)
    """
    anio = extract('year', RegistroEnergetico.fecha_hora).label('anio')
    hora = extract('hour', RegistroEnergetico.fecha_hora)

    banda_horaria = case(
        (hora.between(11, 13), 'Pico Diurno (11am - 1pm)'),
        (hora.between(18, 22), 'Pico Nocturno (6pm - 10pm)'),
        else_='Fuera de Pico'
    ).label('banda')

    picos = db.query(
        anio,
        banda_horaria,
        func.max(RegistroEnergetico.demanda_total_mw).label('demanda_maxima')
    ).group_by(anio, banda_horaria).order_by(anio, banda_horaria).all()

    respuesta = {}
    for fila in picos:
        if fila.banda == 'Fuera de Pico':
            continue
        
        anio_int = int(fila.anio)
        
        if anio_int not in respuesta:
            respuesta[anio_int] = {}
            
        respuesta[anio_int][fila.banda] = {
            "potencia_maxima_mw": round(fila.demanda_maxima, 2) if fila.demanda_maxima else 0.0
        }

    return {
        "analisis": "Picos máximos de demanda por bandas de carga históricas",
        "datos_por_anio": respuesta
    }

@app.get("/api/v1/analitica/factor-carga")
def obtener_factor_carga(db: Session = Depends(get_db)):
    """
    Calcula el Factor de Carga Interanual de la red eléctrica global.
    Fórmula: (Demanda Promedio / Demanda Máxima) * 100 para cada año.
    """
    anio = extract('year', RegistroEnergetico.fecha_hora).label('anio')

    metricas_anuales = db.query(
        anio,
        func.avg(RegistroEnergetico.demanda_total_mw).label('demanda_promedio'),
        func.max(RegistroEnergetico.demanda_total_mw).label('demanda_maxima')
    ).group_by('anio').order_by('anio').all()

    respuesta = []
    for fila in metricas_anuales:
        if fila.demanda_maxima and fila.demanda_maxima > 0:
            # Aplicamos la ecuación de ingeniería eléctrica
            factor_carga = (fila.demanda_promedio / fila.demanda_maxima) * 100
        else:
            factor_carga = 0.0

        respuesta.append({
            "anio": int(fila.anio),
            "demanda_promedio_mw": round(fila.demanda_promedio, 2),
            "demanda_maxima_mw": round(fila.demanda_maxima, 2),
            "factor_de_carga_porcentaje": round(factor_carga, 2)
        })

    return {
        "metrica": "Factor de Carga Interanual Global",
        "descripcion": "Un porcentaje alto indica estabilidad en el consumo; valores bajos exigen plantas pico.",
        "historico": respuesta
    }

@app.get("/api/v1/analitica/sensibilidad-termica")
def obtener_sensibilidad_termica(db: Session = Depends(get_db)):
    """
    Calcula la covarianza y varianza para determinar el impacto cuantitativo
    de las temperaturas extremas sobre el pico de demanda de la red.
    """
    query = """
        with estadisticas as (
            select 
                avg(demanda_total_mw) as avg_d,
                avg(temperatura_max_c) as avg_t
            from registro_energetico
            where temperatura_max_c is not null
        )
        select 
            sum((temperatura_max_c - avg_t) * (demanda_total_mw - avg_d)) / 
            sum(power(temperatura_max_c - avg_t, 2)) as factor_sensibilidad_beta
        from registro_energetico, estadisticas
        where temperatura_max_c is not null;
    """
    resultado = db.execute(text(query)).fetchone()
    factor_beta = resultado[0] if resultado and resultado[0] else 0.0

    return {
        "metrica": "Factor de Sensibilidad Térmica Global",
        "impacto_cuantitativo": f"Por cada 1°C de incremento térmico, la demanda del sistema aumenta un estimado de {round(factor_beta, 2)} MW.",
        "coeficiente_beta": round(factor_beta, 4)
    }



@app.post("/api/v1/auth/registrar", response_model=TokenResponse, status_code=201)
def registrar_usuario(user_data: UserRegister, db: Session = Depends(get_db)):
    print(f"\n🔍 [DEBUG] Intentando registrar a: {user_data.email}")
    
    try:
        usuario_existente = db.query(Usuario).filter(Usuario.email == user_data.email).first()
        if usuario_existente:
            print("⚠️ [DEBUG] El usuario ya existe en la BD.")
            raise HTTPException(status_code=400, detail="El correo ya existe.")

        print("🔑 [DEBUG] Generando hash de contraseña...")
        password_encriptada = obtener_password_hash(user_data.password)

        rol_str = user_data.rol.value if hasattr(user_data.rol, 'value') else str(user_data.rol)

        print(f" [DEBUG] Guardando en la tabla 'usuarios' con rol: {rol_str}...")
        nuevo_usuario = Usuario(
            nombre=user_data.nombre,
            email=user_data.email,
            hashed_password=password_encriptada,
            rol=rol_str
        )

        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        print(" [DEBUG] Usuario guardado exitosamente en Postgres!")

        token_jwt = crear_token_acceso(datos={"sub": nuevo_usuario.email, "rol": nuevo_usuario.rol})
        return {"access_token": token_jwt, "token_type": "bearer"}

    except Exception as e:
        print(f" [ERROR CRÍTICO CAPTURADO]: {type(e).__name__} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login_operador(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Ruta de inicio de sesión estándar de OAuth2.
    El campo 'username' corresponde al correo electrónico del operador.
    """
    usuario = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    
    if not usuario or not usuario.activo:
        raise HTTPException(
            status_code=400,
            detail="Credenciales de acceso incorrectas o usuario inactivo."
        )

    if not verificar_password(form_data.password, usuario.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Credenciales de acceso incorrectas."
        )

    token_jwt = crear_token_acceso(datos={"sub": usuario.email, "rol": usuario.rol})
    
    return {"access_token": token_jwt, "token_type": "bearer"}


# --- ENDPOINT ANALÍTICO: IMPACTO CLIMATOLÓGICO Y SENSIBILIDAD TÉRMICA ---
@app.get("/api/v1/analitica/impacto-climatico")
def obtener_impacto_climatico(db: Session = Depends(get_db)):
    """
    Agrupa los datos por día para obtener la T_máxima, T_mínima y el Pico de Demanda del día.
    Calcula la correlación de Pearson y el incremento de MW por cada grado Celsius (°C).
    """
    query = text("""
        WITH datos_diarios AS (
            SELECT 
                DATE(fecha_hora) AS fecha,
                MAX(temperatura_max_c) AS temp_max,
                MIN(temperatura_min_c) AS temp_min,
                MAX(demanda_total_mw) AS demanda_pico
            FROM registro_energetico
            WHERE temperatura_max_c IS NOT NULL
            GROUP BY DATE(fecha_hora)
        ),
        stats AS (
            SELECT 
                AVG(temp_max) AS avg_t,
                AVG(demanda_pico) AS avg_d,
                COUNT(*) AS n
            FROM datos_diarios
        )
        SELECT 
            d.fecha,
            d.temp_max,
            d.temp_min,
            d.demanda_pico,
            -- Pendiente Beta 1 (MW extra por cada °C)
            SUM((d.temp_max - s.avg_t) * (d.demanda_pico - s.avg_d)) OVER() / 
            NULLIF(SUM(POWER(d.temp_max - s.avg_t, 2)) OVER(), 0) AS factor_beta,
            -- Correlación de Pearson
            CORR(d.temp_max, d.demanda_pico) OVER() AS correlacion
        FROM datos_diarios d, stats s
        ORDER BY d.fecha ASC;
    """)
    
    resultados = db.execute(query).fetchall()
    
    if not resultados:
        return {"mensaje": "No se encontraron datos climatológicos."}

    # Formateamos los datos para el frontend
    registros = []
    factor_beta = resultados[0].factor_beta or 0.0
    correlacion = resultados[0].correlacion or 0.0

    for fila in resultados:
        registros.append({
            "fecha": str(fila.fecha),
            "temp_max_c": round(fila.temp_max, 2),
            "temp_min_c": round(fila.temp_min, 2),
            "demanda_pico_mw": round(fila.demanda_pico, 2)
        })

    return {
        "analisis_cuantitativo": {
            "factor_sensibilidad_mw_por_grado": round(factor_beta, 2),
            "coeficiente_correlacion": round(correlacion, 4),
            "diagnostico": f"Por cada 1°C que aumenta la temperatura máxima, el pico de demanda del sistema se incrementa aproximadamente en {round(factor_beta, 2)} MW debido al uso intensivo de climatización/HVAC."
        },
        "historico_diario": registros
    }