import os
import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Biwenger Stats & Mercado", page_icon="⚽", layout="wide"
)


# Cargar datos con caché
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

    # Filtrar solo compras puras al mercado
    df_mercado = df[
        (df["Vendedor"] == "Mercado")
        & (df["Tipo"] == "market")
        & (df["Precio Operación"] >= df["Valor Mercado"])
    ].copy()

    # Calcular métricas
    df_mercado["Sobreprecio (€)"] = (
        df_mercado["Precio Operación"] - df_mercado["Valor Mercado"]
    )
    df_mercado["Sobreprecio (%)"] = (
        df_mercado["Sobreprecio (€)"] / df_mercado["Valor Mercado"]
    ) * 100

    # Métricas adaptadas a móvil
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Operaciones Mercado", f"{len(df_mercado)}")
    c2.metric("Sobrepuja Media Real", f"+{df_mercado['Sobreprecio (%)'].mean():.1f}%")
    c3.metric(
        "Sobrepuja Mediana Real", f"+{df_mercado['Sobreprecio (%)'].median():.1f}%"
    )

    st.divider()

    # Gráfico de Fichajes Caros
    st.subheader("🔥 Top 10 Fichajes Más Caros del Mercado")
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

    # 1. FILTRO DE COMPRAS PURAS DE MERCADO (Sin clausulazos ni ventas)
    df_compras_puras = df[
        (df["Vendedor"] == "Mercado")
        & (df["Tipo"] == "market")
        & (df["Precio Operación"] >= df["Valor Mercado"])
    ].copy()

    # Calcular sobrepujas reales
    df_compras_puras["Sobreprecio (€)"] = (
        df_compras_puras["Precio Operación"] - df_compras_puras["Valor Mercado"]
    )
    df_compras_puras["Sobreprecio (%)"] = (
        df_compras_puras["Sobreprecio (€)"] / df_compras_puras["Valor Mercado"]
    ) * 100

    # Selector de Rival
    lista_rivales = sorted(df_compras_puras["Comprador"].unique().tolist())
    rival_seleccionado = st.selectbox("🔍 Selecciona un Rival:", lista_rivales)

    # Filtrar datos del rival elegido
    df_rival_compras = df_compras_puras[
        df_compras_puras["Comprador"] == rival_seleccionado
    ]

    st.divider()

    # --- SECCIÓN A: COMPRAS Y SOBREPUJAS ---
    st.subheader(f"🛒 Fichajes y Pujas de {rival_seleccionado}")

    col1, col2, col3 = st.columns(3)
    gastado_total = df_rival_compras["Precio Operación"].sum()
    sobrepuja_media = df_rival_compras["Sobreprecio (%)"].mean()
    fichajes_totales = len(df_rival_compras)

    col1.metric("Inversión en Mercado", f"{gastado_total:,.0f} €")
    col2.metric("Nº Fichajes Reales", f"{fichajes_totales}")
    col3.metric(
        "Sobrepuja Media Real",
        f"+{sobrepuja_media:.1f}%" if pd.notnull(sobrepuja_media) else "0%",
    )

    # Gráfico Top Fichajes (Solo Compras Puras)
    if not df_rival_compras.empty:
        fig_rival = px.bar(
            df_rival_compras.nlargest(8, "Precio Operación"),
            x="Jugador",
            y="Precio Operación",
            text_auto=".2s",
            color="Sobreprecio (%)",
            color_continuous_scale="Reds",
            title=f"Principales Pujas de {rival_seleccionado}",
        )
        fig_rival.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=350)
        st.plotly_chart(fig_rival, use_container_width=True)

        # Tabla de Compras Limpia
        st.dataframe(
            df_rival_compras[
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

    st.divider()

    # --- SECCIÓN B: VENTAS Y DESINVERSIONES ---
    st.subheader(f"💰 Ventas Realizadas por {rival_seleccionado}")

    # Filtrar cuando el rival actúa como VENDEDOR
    df_rival_ventas = df[df["Vendedor"] == rival_seleccionado].copy()

    if df_rival_ventas.empty:
        st.info("Este manager aún no ha realizado ventas registradas.")
    else:
        total_ingresado = df_rival_ventas["Precio Operación"].sum()
        ventas_totales = len(df_rival_ventas)

        col_v1, col_v2 = st.columns(2)
        col_v1.metric("Total Ingresado por Ventas", f"{total_ingresado:,.0f} €")
        col_v2.metric("Nº de Ventas", f"{ventas_totales}")

        st.dataframe(
            df_rival_ventas[
                ["Fecha", "Jugador", "Comprador", "Precio Operación", "Tipo"]
            ],
            hide_index=True,
            use_container_width=True,
        )
