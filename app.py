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
# PESTAÑA 3: RIVALES (Análisis por Manager)
# ==========================================
with tab_rivales:
    st.header("👥 Análisis de Rivales y Competencia")

    # Filtrar solo compras
    df_compras = df[df["Vendedor"] == "Mercado"].copy()

    if "Sobreprecio (€)" not in df_compras.columns:
        df_compras["Sobreprecio (€)"] = (
            df_compras["Precio Operación"] - df_compras["Valor Mercado"]
        )
    if "Sobreprecio (%)" not in df_compras.columns:
        df_compras["Sobreprecio (%)"] = (
            df_compras["Sobreprecio (€)"] / df_compras["Valor Mercado"]
        ) * 100

    # Selector de Rival (adaptado a móvil)
    lista_rivales = sorted(df_compras["Comprador"].unique().tolist())
    rival_seleccionado = st.selectbox("🔍 Selecciona un Rival:", lista_rivales)

    # Filtrar datos del rival elegido
    df_rival = df_compras[df_compras["Comprador"] == rival_seleccionado]

    st.divider()

    # Métricas clave del rival
    col1, col2, col3 = st.columns(3)
    gastado_total = df_rival["Precio Operación"].sum()
    sobrepuja_media_rival = df_rival["Sobreprecio (%)"].mean()
    fichajes_rival = len(df_rival)

    col1.metric("Gasto Total Mercado", f"{gastado_total:,.0f} €")
    col2.metric("Nº de Fichajes", f"{fichajes_rival}")
    col3.metric("Sobrepuja Media", f"+{sobrepuja_media_rival:.1f}%")

    # Gráfico de sus compras más caras
    st.subheader(f"📌 Principales Fichajes de {rival_seleccionado}")
    fig_rival = px.bar(
        df_rival.nlargest(8, "Precio Operación"),
        x="Jugador",
        y="Precio Operación",
        text_auto=".2s",
        color="Sobreprecio (%)",
        color_continuous_scale="Reds",
    )
    fig_rival.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=350,
    )
    st.plotly_chart(fig_rival, use_container_width=True)

    # Tabla detallada del rival
    st.dataframe(
        df_rival[
            [
                "Fecha",
                "Jugador",
                "Precio Operación",
                "Valor Mercado",
                "Sobreprecio (%)",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )
