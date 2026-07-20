import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# Configuración criptográfica
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "SUPER_SECRET_KEY_PARA_DEGRID_2026_CAMBIAME")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Contexto para encriptar contraseñas usando bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 1. Funciones de verificación y hashing de contraseñas
def verificar_password(plain_password: str, hashed_password: str) -> bool:
    """Compara una contraseña en texto plano con su hash en la BD."""
    return pwd_context.verify(plain_password, hashed_password)

def obtener_password_hash(password: str) -> str:
    """Genera un hash seguro irreversible a partir de una contraseña."""
    return pwd_context.hash(password)

# 2. Función clave: Generación del Token JWT
def crear_token_acceso(datos: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Empaqueta los datos del usuario (ID, email, Rol) dentro de un token 
    firmado que expirará en el tiempo configurado.
    """
    datos_a_cifrar = datos.copy()
    
    # Tiempo de vida del token
    if expires_delta:
        tiempo_expiracion = datetime.now(timezone.utc) + expires_delta
    else:
        tiempo_expiracion = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Añadimos la fecha de expiración al cuerpo del token (payload)
    datos_a_cifrar.update({"exp": tiempo_expiracion})
    
    # Firmamos el token con nuestra clave secreta
    token_firmado = jwt.encode(datos_a_cifrar, SECRET_KEY, algorithm=ALGORITHM)
    return token_firmado