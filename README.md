# DeGrid: Plataforma de Observabilidad y Análisis del Consumo Energético 

DeGrid une el historial de consumo eléctrico con los datos del clima para responder a una pregunta clave: ¿cuánto más sufre la red cuando aprieta el calor?

A través de una arquitectura con PostgreSQL, FastAPI y un tablero visual interactivo, la plataforma analiza cómo influyen las altas temperaturas en el uso de equipos de aire acondicionado y refrigeración, calculando exactamente cuántos megavatios (MW) extra se consumen por cada grado que sube el termómetro. En lugar de lidiar con datos aislados, transformamos millones de registros en métricas claras que facilitan el diagnóstico y la toma de decisiones en la gestión de la red eléctrica.

##  Guía de Instalación y Uso

### Requisitos Previos
- Python 3.10+
- PostgreSQL 15+ (local o en contenedor)
- Streamlit (para el dashboard)
- Docker & Docker Compose (opcional, para despliegue)

### Paso 1: Generar Datos Sintéticos

Crea el archivo CSV con datos históricos sintéticos de consumo energético:

```bash
python generador_de_datos.py
```

Esto generará `data/datos_energia.csv` con 20 años de registros horarios de consumo.

### Paso 2: Ingestar Datos en PostgreSQL

Carga los datos sintéticos en la base de datos y enriquécelos con información climática:

```bash
cd backend_api
python etl_pipeline.py
python polar_temperatura.py
```

**Nota:** Asegúrese de que PostgreSQL esté corriendo y que `.env` tenga las credenciales correctas.

### Paso 3: Iniciar la API REST

Arranca el servidor FastAPI:

```bash
cd backend_api
python -m uvicorn main:app --reload
```

La API estará disponible en `http://localhost:8000`
- Documentación interactiva: `http://localhost:8000/docs`

### Paso 4: Iniciar el Dashboard

En una nueva terminal, instala dependencias y ejecuta el servidor React:

```bash
streamlit run dashboard.py
```

El dashboard se abrirá en `http://localhost:3000`

## Fases del Proyecto

El desarrollo está estructurado en tres fases principales:

**FASE 1: Infraestructura Base e Ingestión Histórica**
* **Generación Sintética y Limpieza:** Pipeline ETL en Python (Pandas) para procesar simulaciones de consumo de múltiples circuitos.
* **Almacenamiento Optimizado:** Base de datos relacional particionada por rangos de fechas en PostgreSQL para garantizar un rendimiento analítico rápido sobre grandes volúmenes de datos temporales.

**FASE 2: Interfaz, Persistencia Avanzada e Integración Externa** 
* **Capa de Persistencia (ORM):** Implementación de SQLAlchemy/Alembic para aislar por completo el código de la base de datos de la lógica de negocio.
* **Gestión de Usuarios:** Módulo de sesiones seguro diferenciado por niveles de acceso territorial.
* **Factor Climático Externo:** Cruce de datos con variaciones térmicas para calcular el multiplicador de demanda energética en horarios de picos de calor.

**FASE 3: API REST, Containerización y DataOps** 
* **Microservicios:** Estructuración de la solución en contenedores Docker desacoplados para asegurar portabilidad absoluta.
* **API REST:** Desarrollo de endpoints seguros para proveer analítica avanzada y permitir registros interactivos (CRUD).
* **Orquestación:** Despliegue mediante `docker-compose`, parametrizando credenciales de forma segura fuera del código fuente.

## 🛠️ Stack Tecnológico

* **Base de Datos:** PostgreSQL 15 (Particionamiento nativo)
* **Backend & API:** Python 3.10, FastAPI, SQLAlchemy, Alembic, Pandas
* **Frontend Dashboard:** React, CSS, Chart.js / Recharts
* **DataOps:** Docker, Docker Compose

