import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def load_dotenv(dotenv_path: str = ".env") -> None:
    """Carga las variables de entorno desde un archivo .env"""
    env_file = Path(dotenv_path)
    if not env_file.exists():
        return

    with env_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


# Cargar variables de entorno
load_dotenv()

# Obtener y validar DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no definida. Añade DATABASE_URL en .env o en las variables de entorno.")

# Crear engine de SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
