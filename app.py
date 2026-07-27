import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Panel Financiero & Mercado Biwenger",
    page_icon="⚽",
    layout="wide",
)

st.title("⚽ Panel Financiero & Mercado Biwenger")
st.caption("Análisis en tiempo real de sobrepujas, fichajes y presupuestos.")


# Función para cargar los datos
@st.cache_data(ttl=300)  # Recarga datos cada 5 minutos
def load_data():
    file_csv = "historial_biwenger_completo.csv"
    file_xlsx = "historial_biwenger_completo.xlsx"

    if os.path.exists(file_csv):
        return pd.read_csv(file_csv)
    elif os.path.exists(file_xlsx):
        return pd.read_excel(file_xlsx)
    else:
        return None


df = load_data()

if df is None or df.empty:
    st.info("Cargando datos o esperando primera actualización del CSV...")
else:
    st.success(f"¡Datos cargados con éxito! ({len(df)} registros)")
    # Aquí va el resto de tus gráficos, tablas y métricas
    st.dataframe(df.head(10))
