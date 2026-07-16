# DeGrid: Plataforma de Observabilidad y Análisis del Consumo Energético 

DeGrid es un sistema integral de ingeniería de datos a gran escala enfocado en procesar y analizar series de tiempo de alta frecuencia, balances de carga, eficiencia de generación y comportamiento de la red eléctrica.

Este proyecto implementa un pipeline completo de datos, desde la generación e ingestión de un histórico masivo (20 años de registros horarios), hasta su persistencia avanzada y visualización mediante una arquitectura de microservicios.

## Fases del Proyecto

El desarrollo está estructurado en tres fases principales:

FASE 1: Infraestructura Base e Ingestión Histórica
* **Generación Sintética y Limpieza:** Pipeline ETL en Python (Pandas) para procesar simulaciones de consumo de múltiples circuitos.
* **Almacenamiento Optimizado:** Base de datos relacional particionada por rangos de fechas en PostgreSQL para garantizar un rendimiento analítico rápido sobre grandes volúmenes de datos temporales.

### FASE 2: Interfaz, Persistencia Avanzada e Integración Externa 
* **Capa de Persistencia (ORM):** Implementación de SQLAlchemy/Alembic para aislar por completo el código de la base de datos de la lógica de negocio.
* **Gestión de Usuarios:** Módulo de sesiones seguro diferenciado por niveles de acceso territorial.
* **Factor Climático Externo:** Cruce de datos con variaciones térmicas para calcular el multiplicador de demanda energética en horarios de picos de calor.

### FASE 3: API REST, Containerización y DataOps 
* **Microservicios:** Estructuración de la solución en contenedores Docker desacoplados para asegurar portabilidad absoluta.
* **API REST:** Desarrollo de endpoints seguros para proveer analítica avanzada y permitir registros interactivos (CRUD).
* **Orquestación:** Despliegue mediante `docker-compose`, parametrizando credenciales de forma segura fuera del código fuente.

## 🛠️ Stack Tecnológico

* **Base de Datos:** PostgreSQL 15 (Particionamiento nativo)
* **Backend & API:** Python 3.10, FastAPI, SQLAlchemy, Alembic, Pandas
* **Frontend Dashboard:** React, CSS, Chart.js / Recharts
* **DataOps:** Docker, Docker Compose

## 📁 Estructura del Repositorio

```text
EnerFlow/
├── backend_api/               # Lógica de negocio y Endpoints REST
│   ├── models.py              # Modelos ORM (SQLAlchemy)
│   ├── main.py                # Aplicación FastAPI
│   ├── etl_pipeline.py        # Script de ingestión de datos
│   └── Dockerfile             # Contenedor del backend
├── frontend_app/              # Interfaz de usuario analítica en React
│   ├── src/                   # Componentes y estilos
│   ├── package.json
│   └── Dockerfile             # Contenedor del frontend
├── docker-compose.yml         # Orquestador principal
├── .env.example               # Plantilla de variables de entorno
└── README.md                  # 