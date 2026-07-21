from sqlalchemy import text
from database import engine

print("🌡️ Iniciando inyección de temperaturas estacionales en PostgreSQL...")

sql = text("""
    UPDATE registro_energetico 
    SET 
        temperatura_max_c = ROUND((24 + 11 * SIN((EXTRACT(doy FROM fecha_hora) - 80) * 2 * PI() / 365) + (RANDOM() * 4 - 2))::numeric, 2),
        temperatura_min_c = ROUND((14 + 9 * SIN((EXTRACT(doy FROM fecha_hora) - 80) * 2 * PI() / 365) + (RANDOM() * 3 - 1.5))::numeric, 2);
""")

try:
    with engine.begin() as conexion:
        resultado = conexion.execute(sql)
        print(f"✅ ¡Éxito absoluto! Se actualizaron {resultado.rowcount:,} filas con datos de temperatura.")
except Exception as e:
    print(f"❌ Ocurrió un error al actualizar: {e}")