import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, time

# Configuración de la página del Dashboard
st.set_page_config(
    page_title="DeGrid Analytics - Panel de Control",
    page_icon="⚡",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000/api/v1"

st.title("⚡ DeGrid: Sistema de Balances y Matriz Energética Histórica")
st.markdown("Control analítico y supervisión de cargas del sistema eléctrico interconectado.")

# --- BARRA LATERAL: INTERFACES DE CONTROL (FILTROS) ---
st.sidebar.header("🎛️ Filtros de Control")

# 1. Traer circuitos dinámicamente desde la API
try:
    res_circuitos = requests.get(f"{API_URL}/circuitos")
    lista_circuitos = res_circuitos.json()
except Exception:
    lista_circuitos = []
    st.sidebar.error("No se pudo conectar con la API del Backend.")

# Selector de Circuito (Añadimos opción de ver todos)
circuito_seleccionado = st.sidebar.selectbox(
    "Selecciona un Circuito:",
    options=["Todos los Circuitos"] + lista_circuitos
)

# Selector de Rango de Fechas
st.sidebar.subheader("📅 Rango de Análisis")
fecha_inicio = st.sidebar.date_input("Fecha Inicial:", datetime(2004, 1, 1))
fecha_fin = st.sidebar.date_input("Fecha Final:", datetime(2004, 1, 7))

# --- CONSULTA DE DATOS A LA API ---
circuito_param = "" if circuito_seleccionado == "Todos los Circuitos" else circuito_seleccionado
params = {
    "start_date": f"{fecha_inicio}T00:00:00",
    "end_date": f"{fecha_fin}T23:59:59",
    "circuito": circuito_param
}

with st.spinner("Pidiendo métricas en tiempo real al backend..."):
    try:
        respuesta = requests.get(f"{API_URL}/energia/metricas", params=params)
        datos_json = respuesta.json()
        df = pd.DataFrame(datos_json.get("datos", []))
    except Exception as e:
        df = pd.DataFrame()

# --- VALIDACIÓN DE DATOS ---
if df.empty:
    st.warning("⚠️ No se encontraron registros para los filtros seleccionados o el backend está apagado.")
else:
    # Ordenamos y formateamos columnas
    df['fecha'] = pd.to_datetime(df['fecha'])
    df = df.sort_values('fecha')

    # --- PANELES MÉTRICOS PRINCIPALES (CONTROL DE BALANCES) ---
    st.subheader("📊 Balance Energético del Periodo")
    
    gen_total = (df['generacion_solar_mw_total'].sum() + 
                 df['generacion_termoelectrica_mw_total'].sum() + 
                 df['generacion_bloques_flotantes_mw_total'].sum())
    demanda_total = df['demanda_total_mw_total'].sum()
    balance = gen_total - demanda_total

    col1, col2, col3 = st.columns(3)
    col1.metric("Generación Total Acumulada", f"{round(gen_total, 2):,} MW")
    col2.metric("Demanda Total Solicitada", f"{round(demanda_total, 2):,} MW")
    
    if balance >= 0:
        col3.metric("Balance de Red (Superávit)", f"+{round(balance, 2):,} MW", delta_color="normal")
    else:
        col3.metric("Balance de Red (Déficit / Pérdidas)", f"{round(balance, 2):,} MW", delta_color="inverse")

    st.markdown("---")

    # --- DISEÑO DE GRÁFICOS ---
    izq_col, der_col = st.columns(2)

    with izq_col:
        st.subheader("📈 Curva de Carga Eléctrica (Demanda)")
        st.markdown("*Evolución temporal del comportamiento del consumo en la ventana analizada.*")
        
        # Generación de la curva de carga tradicional
        fig_demanda = px.line(
            df, 
            x='fecha', 
            y='demanda_total_mw_total',
            labels={'demanda_total_mw_total': 'Demanda (MW)', 'fecha': 'Tiempo'},
            line_shape='spline',
            render_mode='svg'
        )
        fig_demanda.update_traces(line_color='#FF4B4B', line_width=3)
        st.plotly_chart(fig_demanda, use_container_width=True)

    with der_col:
        st.subheader("🥞 Matriz de Generación Energética")
        st.markdown("*Distribución y aporte de cada fuente tecnológica a la red.*")
        
        # Reformateamos el DataFrame para hacer el gráfico de áreas apiladas (Stacked Area Chart)
        df_melted = df.melt(
            id_vars=['fecha'], 
            value_vars=['generacion_solar_mw_total', 'generacion_termoelectrica_mw_total', 'generacion_bloques_flotantes_mw_total'],
            var_name='Fuente de Energía', 
            value_name='Megavatios (MW)'
        )
        
        # Renombrar leyendas para estética visual
        df_melted['Fuente de Energía'] = df_melted['Fuente de Energía'].str.replace('_mw_total', '').str.replace('generacion_', '').str.title()

        fig_matriz = px.area(
            df_melted, 
            x='fecha', 
            y='Megavatios (MW)', 
            color='Fuente de Energía',
            color_discrete_map={
                'Solar': '#FFD700',
                'Termoelectrica': '#4682B4',
                'Bloques_Flotantes': '#20B2AA'
            }
        )
        st.plotly_chart(fig_matriz, use_container_width=True)