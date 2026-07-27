
import os
import plotly.express as px
import pandas as pd
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Mercado & Sobrepujas - Biwenger", page_icon="📊", layout="wide"
)


# Cargar datos con caché para que vaya rápido en móvil
@st.cache_data(ttl=300)
def load_data():
    csv_file = "historial_biwenger_completo.csv"
    xlsx_file = "historial_biwenger_completo.xlsx"

    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)
    elif os.path.exists(xlsx_file):
        return pd.read_excel(xlsx_file)
    return None


df = load_data()

st.title("📊 Análisis de Mercado y Sobrepujas")
st.caption("Fichajes recientes, sobrepujas medias y rendimiento económico.")

if df is None or df.empty:
    st.warning("⚠️ No se encontraron datos del historial de fichajes.")
    st.stop()

# --- PREPARACIÓN DE DATOS ---
# Filtrar solo compras al Mercado
df_mercado = df[df["Vendedor"] == "Mercado"].copy()

# Calcular sobrepujas si no existen
if "Sobreprecio (€)" not in df_mercado.columns:
    df_mercado["Sobreprecio (€)"] = (
        df_mercado["Precio Operación"] - df_mercado["Valor Mercado"]
    )

if "Sobreprecio (%)" not in df_mercado.columns:
    df_mercado["Sobreprecio (%)"] = (
        df_mercado["Sobreprecio (€)"] / df_mercado["Valor Mercado"]
    ) * 100

# Convertir Fecha a datetime para ordenar
df_mercado["Fecha"] = pd.to_datetime(df_mercado["Fecha"])
df_mercado = df_mercado.sort_values(by="Fecha", ascending=False)

# --- 1. MÉTRICAS CLAVE (Optimizado para Pantalla Táctil) ---
col1, col2, col3 = st.columns(3)

sobrepago_medio_pct = df_mercado["Sobreprecio (%)"].mean()
sobrepago_mediano_pct = df_mercado["Sobreprecio (%)"].median()
total_fichajes = len(df_mercado)

with col1:
    st.metric(
        label="Total Fichajes Mercado", value=f"{total_fichajes} jugadores"
    )

with col2:
    st.metric(
        label="Sobrepuja Media (%)", value=f"+{sobrepago_medio_pct:.1f}%"
    )

with col3:
    st.metric(
        label="Sobrepuja Mediana (%)", value=f"+{sobrepago_mediano_pct:.1f}%"
    )

st.divider()

# --- 2. GRÁFICO INTERACTIVO (Adaptable a Móvil) ---
st.subheader("🔥 Top 10 Fichajes Más Caros del Mercado")

top_fichajes = df_mercado.nlargest(10, "Precio Operación")

fig = px.bar(
    top_fichajes,
    x="Precio Operación",
    y="Jugador",
    color="Comprador",
    orientation="h",
    text_auto=".2s",
    title="",
)

# Ajuste de márgenes para que se vea bien en pantallas verticales
fig.update_layout(
    yaxis={"categoryorder": "total ascending"},
    margin=dict(l=10, r=10, t=20, b=10),
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5),
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- 3. TABLA RESUMEN A PRUEBA DE SCROLL MOLESTO ---
st.subheader("📋 Últimas Operaciones")

# Seleccionamos y formateamos solo las columnas importantes para pantalla pequeña
df_tabla = df_mercado[
    [
        "Fecha",
        "Jugador",
        "Comprador",
        "Precio Operación",
        "Valor Mercado",
        "Sobreprecio (€)",
    ]
].copy()
df_tabla["Fecha"] = df_tabla["Fecha"].dt.strftime("%d/%m/%Y")

# Streamlit muestra la tabla en formato adaptable automáticamente
st.dataframe(df_tabla, hide_index=True, use_container_width=True)
