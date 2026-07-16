import pandas as pd
import numpy as np

def generar_dataset_multicircuito():
    print("Definiendo configuración de los 7 circuitos...")
    
    circuitos_config = {
        'Habana_Vieja_1': 1.0,
        'Plaza_Revolucion_2': 1.4,
        'Playa_Miramar_3': 1.2,
        '10_Octubre_Residencial': 0.9,
        'Mariel_Industrial': 1.8,  
        'Matanzas_Varadero': 1.3,  
        'Artemisa_Pueblo': 0.75     
    }
    
    print("Generando índice temporal base (20 años)...")
    start_date = '2004-01-01'
    end_date = '2023-12-31'
    fechas = pd.date_range(start=start_date, end=end_date, freq='h')
    
    df_tiempo = pd.DataFrame({'fecha_hora': fechas})
    df_tiempo['hora'] = df_tiempo['fecha_hora'].dt.hour
    df_tiempo['dia_del_ano'] = df_tiempo['fecha_hora'].dt.dayofyear

    print("Creando producto cartesiano para los 7 circuitos...")
    # DataFrame con los circuitos
    df_circuitos = pd.DataFrame(list(circuitos_config.items()), columns=['circuito', 'escala_circuito'])
    
    # Operación Cross Join: Multiplica las ~175,000 horas por los 7 circuitos
    # Resultado: ~1.22 millones de filas. ¡Esto ya es Big Data para el proyecto!
    df = df_tiempo.merge(df_circuitos, how='cross')

    print("Simulando variaciones climáticas regionales...")
    # Temperatura base con ligeras variaciones aleatorias por circuito
    temp_anual = 25 + 6 * np.sin(2 * np.pi * (df['dia_del_ano'] - 110) / 365)
    temp_diaria = 4 * np.sin(2 * np.pi * (df['hora'] - 9) / 24)
    ruido_temp = np.random.normal(0, 1.5, len(df))
    
    df['temperatura_c'] = temp_anual + temp_diaria + ruido_temp

    # Factor Climático
    df['multiplicador_clima'] = np.where(
        df['temperatura_c'] > 28,
        1 + (df['temperatura_c'] - 28) * 0.04,
        1.0
    )

    print("Calculando demandas personalizadas por circuito...")
    # La demanda base ahora se multiplica por el factor de escala de cada circuito
    demanda_base_mw = 250 * df['escala_circuito'] 
    
    # Picos de demanda (Campanas de Gauss) con ligeras variaciones por circuito
    pico_diurno = (80 * df['escala_circuito']) * np.exp(-0.5 * ((df['hora'] - 13) / 2.5)**2)
    pico_nocturno = (120 * df['escala_circuito']) * np.exp(-0.5 * ((df['hora'] - 20) / 1.5)**2)
    
    ruido_demanda = np.random.normal(0, 10, len(df))

    # Demanda Final por circuito
    df['demanda_total_mw'] = (demanda_base_mw + pico_diurno + pico_nocturno + ruido_demanda) * df['multiplicador_clima']

    print("Asignando balance de generación...")
    # Generación Solar 
    df['generacion_solar_mw'] = np.where(
        (df['hora'] >= 7) & (df['hora'] <= 18),
        (60 * df['escala_circuito']) * np.exp(-0.5 * ((df['hora'] - 13) / 2)**2),
        0
    )
    df['generacion_solar_mw'] *= np.random.uniform(0.75, 1.0, len(df))

    demanda_restante = df['demanda_total_mw'] - df['generacion_solar_mw']

    # Termoeléctricas (Asignación base por circuito)
    capacidad_max_termo = 300 * df['escala_circuito']
    df['generacion_termoelectrica_mw'] = np.where(
        demanda_restante > capacidad_max_termo,
        capacidad_max_termo,
        demanda_restante
    )

    # Bloques Flotantes (Carga crítica de emergencia)
    df['generacion_bloques_flotantes_mw'] = demanad_restante = demanad_restante = demanda_restante - df['generacion_termoelectrica_mw']
    # Evitar pequeños decimales negativos 
    df['generacion_bloques_flotantes_mw'] = df['generacion_bloques_flotantes_mw'].clip(lower=0)

    print("Limpiando y formateando el dataset final...")
    # Redondeos e indexación
    columnas_numericas = ['temperatura_c', 'demanda_total_mw', 'generacion_solar_mw', 
                          'generacion_termoelectrica_mw', 'generacion_bloques_flotantes_mw']
    df[columnas_numericas] = df[columnas_numericas].round(2)

    # Quitamos columnas de cálculo 
    df = df.drop(columns=['hora', 'dia_del_ano', 'escala_circuito', 'multiplicador_clima'])
    
    # Reordenar columnas 
    df = df[['fecha_hora', 'circuito', 'temperatura_c', 'demanda_total_mw', 
             'generacion_solar_mw', 'generacion_termoelectrica_mw', 'generacion_bloques_flotantes_mw']]

    return df

if __name__ == "__main__":
    dataset_final = generar_dataset_multicircuito()
    
    print("\n--- Guardando el archivo semilla (Seed) ---")
  
    dataset_final.to_csv("datos_energia.csv", index=False)
    
    print(f"¡Éxito! Dataset generado con {len(dataset_final):,} registros.")
    print("\nMuestra de las primeras filas:")
    print(dataset_final.head(10))