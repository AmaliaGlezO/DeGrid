import pandas as pd
from database import engine, SessionLocal
from models import RegistroEnergetico, Base

# 1. Configuración de la "Tubería" (Conexión)
# Importa engine y SessionLocal desde database.py que carga .env automáticamente
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def ejecutar_etl():
    archivo_csv = './data/datos_energia.csv'
    tamano_lote = 10000 
    
    print(f"Iniciando la extracción del embalse: {archivo_csv}")
    
    # Abrimos la sesión con la base de datos
    with SessionLocal() as db_session:
        
        # 2. La "Bomba de Agua" (Lectura por lotes)
        # pd.read_csv con chunksize devuelve un iterador, no carga todo el archivo.
        iterador_lotes = pd.read_csv(archivo_csv, chunksize=tamano_lote)
        
        lote_num = 1
        for lote_df in iterador_lotes:
            print(f"Procesando lote número {lote_num}...")
            
            # Aseguramos que la columna de tiempo sea un objeto DateTime real
            lote_df['fecha_hora'] = pd.to_datetime(lote_df['fecha_hora'], utc=True)
            
            # 3. Transformación a formato compatible con el ORM
            # Convertimos el DataFrame a una lista de diccionarios
            registros_diccionarios = lote_df.to_dict(orient='records')
            
            # 4. Inserción Masiva (Bulk Insert)
            # bulk_insert_mappings es extremadamente rápido porque omite la creación 
            # de objetos individuales de Python por cada fila.
            db_session.bulk_insert_mappings(RegistroEnergetico, registros_diccionarios)
            
            # Guardamos el lote en la base de datos
            db_session.commit()
            
            lote_num += 1

    print("¡Ingesta de datos completada con éxito!")

if __name__ == "__main__":
    ejecutar_etl()