import streamlit as st
import pandas as pd
import glob
import os

# --- Configuración de Página ---
st.set_page_config(page_title="Gestor de Operaciones Biwenger", layout="wide")

# --- Función de Carga de Datos Automática ---
@st.cache_data(ttl=60)
def load_data():
    # Busca todos los CSV y XLSX en el directorio
    files = glob.glob('*.csv') + glob.glob('*.xlsx')
    
    if not files:
        return None, None
    
    # Selecciona el archivo con la fecha de modificación más reciente
    latest_file = max(files, key=os.path.getmtime)
    
    try:
        if latest_file.endswith('.csv'):
            df = pd.read_csv(latest_file)
        else:
            df = pd.read_excel(latest_file)
        return df, latest_file
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None, None

# --- Interfaz de Usuario ---
st.title("📊 Historial de Operaciones Biwenger")

# Botón para refrescar
if st.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()

# Carga de datos
df, filename = load_data()

if df is None:
    st.warning("No se encontraron archivos de datos. Asegúrate de haber subido tu exportación de Biwenger (.csv o .xlsx) a la carpeta de la app.")
else:
    st.caption(f"📌 Estás viendo los datos del archivo más reciente: **{filename}**")
    
    # Mostrar datos
    st.dataframe(df, use_container_width=True)

    # --- Análisis básico ---
    st.subheader("Resumen de hoy")
    
    # Intentamos detectar la columna de fecha automáticamente
    fecha_col = [col for col in df.columns if 'Fecha' in col]
    
    if fecha_col:
        col_name = fecha_col[0]
        df[col_name] = pd.to_datetime(df[col_name])
        
        # Filtrar por el día de hoy (7 de agosto de 2026)
        hoy = pd.to_datetime('2026-08-07')
        df_hoy = df[df[col_name].dt.date == hoy.date()]
        
        if not df_hoy.empty:
            st.write(f"Se han encontrado {len(df_hoy)} operaciones hoy:")
            st.table(df_hoy)
        else:
            st.info("No hay operaciones registradas para el día de hoy.")
    else:
        st.error("No se pudo encontrar una columna de fecha en el archivo.")
