import os
import plotly.express as px
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Biwenger Stats & Mercado", page_icon="⚽", layout="wide"
)


# Cargar datos
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

# Encabezado Principal
st.title("⚽ Panel Financiero & Mercado Biwenger")
st.caption("Análisis en tiempo real de sobrepujas, fichajes y presupuestos.")

if df is None or df.empty:
    st.info("Cargando datos o esperando primera actualización...")
    st.stop()

# --- PESTAÑAS DE NAVEGACIÓN (Perfecto para Móvil y PC) ---
tab_inicio, tab_mercado, tab_rivales = st.tabs(
    ["🏠 Inicio", "📊 Mercado & Pujas", "👥 Rivales"]
)

# ==========================================
# PESTAÑA 1: INICIO (Resumen General)
# ==========================================
with tab_inicio:
    st.success(f"¡Datos cargados con éxito! ({len(df)} registros)")

    # Tabla Resumen
    st.subheader("📋 Últimos Movimientos")
    st.dataframe(df.head(10), hide_index=True, use_container_width=True)

# ==========================================
# PESTAÑA 2: MERCADO & SOBREPUJAS
# ==========================================
with tab_mercado:
    st.header("📊 Análisis de Mercado")

    df_mercado = df[df["Vendedor"] == "Mercado"].copy()

    # Calcular métricas si faltan
    if "Sobreprecio (€)" not in df_mercado.columns:
        df_mercado["Sobreprecio (€)"] = (
            df_mercado["Precio Operación"] - df_mercado["Valor Mercado"]
        )
    if "Sobreprecio (%)" not in df_mercado.columns:
        df_mercado["Sobreprecio (%)"] = (
            df_mercado["Sobreprecio (€)"] / df_mercado["Valor Mercado"]
        ) * 100

    # Métricas adaptadas a móvil
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Operaciones", f"{len(df_mercado)}")
    c2.metric("Sobrepuja Media", f"+{df_mercado['Sobreprecio (%)'].mean():.1f}%")
    c3.metric(
        "Sobrepuja Mediana", f"+{df_mercado['Sobreprecio (%)'].median():.1f}%"
    )

    st.divider()

    # Gráfico de Fichajes Caros
    st.subheader("🔥 Top 10 Fichajes Más Caros")
    top10 = df_mercado.nlargest(10, "Precio Operación")

    fig = px.bar(
        top10,
        x="Precio Operación",
        y="Jugador",
        color="Comprador",
        orientation="h",
        text_auto=".2s",
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=10, r=10, t=20, b=10),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# PESTAÑA 3: RIVALES (En construcción)
# ==========================================
with tab_rivales:
    st.header("👥 Análisis por Manager")
    st.info("Próximamente: Estadísticas individuales de cada rival.")
