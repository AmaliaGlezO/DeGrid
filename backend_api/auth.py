# auth.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "SUPER_SECRET_KEY_PARA_DEGRID_2026_CAMBIAME")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🛑 FUNCIÓN AUXILIAR PARA PREVENIR EL LÍMITE DE BCRYPT
def _truncar_password(password: str) -> str:
    """
    Bcrypt tiene un límite estricto de 72 bytes.
    Truncamos los bytes de forma limpia sin romper caracteres UTF-8.
    """
    password_bytes = password.encode('utf-8')[:72]
    return password_bytes.decode('utf-8', errors='ignore')

# 1. Funciones de verificación y hashing actualizadas
def verificar_password(plain_password: str, hashed_password: str) -> bool:
    """Compara una contraseña en texto plano con su hash en la BD."""
    return pwd_context.verify(_truncar_password(plain_password), hashed_password)

def obtener_password_hash(password: str) -> str:
    """Genera un hash seguro irreversible a partir de una contraseña."""
    return pwd_context.hash(_truncar_password(password))

# 2. Generación del Token JWT (Se mantiene igual)
def crear_token_acceso(datos: dict, expires_delta: Optional[timedelta] = None) -> str:
    datos_a_cifrar = datos.copy()
    if expires_delta:
        tiempo_expiracion = datetime.now(timezone.utc) + expires_delta
    else:
        tiempo_expiracion = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    datos_a_cifrar.update({"exp": tiempo_expiracion})
    token_firmado = jwt.encode(datos_a_cifrar, SECRET_KEY, algorithm=ALGORITHM)
    return token_firmado