import os
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Configuración de la página
st.set_page_config(
    page_title="Biwenger Stats & Mercado", page_icon="⚽", layout="wide"
)

# 2. CSS personalizado para compactar el espacio superior e interlineado
st.markdown(
    """
    <style>
        /* Compactar margen superior de la app */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1rem !important;
        }
        /* Disminuir tamaño del título e interlineado */
        h1 {
            font-size: 1.8rem !important;
            padding-bottom: 0rem !important;
        }
        h2, h3 {
            font-size: 1.2rem !important;
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        /* Reducir espacio entre divisores */
        hr {
            margin-top: 0.8rem !important;
            margin-bottom: 0.8rem !important;
        }
    </style>
""",
    unsafe_allow_html=True,
)


# Función para formatear números en formato financiero español (ej. 3.636.363 €)
def fmt(val):
    if pd.isna(val) or val is None:
        return "-"
    return f"{val:,.0f} €".replace(",", "X").replace(".", ",").replace("X", ".")


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

# Encabezado Principal compacto
st.title("⚽ Panel Financiero & Mercado Biwenger")

if df is None or df.empty:
    st.info("Cargando datos o esperando primera actualización...")
    st.stop()

# --- PESTAÑAS DE NAVEGACIÓN ---
tab_inicio, tab_mercado, tab_rivales = st.tabs(
    ["🏠 Inicio", "📊 Mercado & Pujas", "👥 Rivales & Cláusulas"]
)

# ==========================================
# PESTAÑA 1: INICIO (Resumen General)
# ==========================================
with tab_inicio:
    st.caption(f"¡Datos cargados con éxito! ({len(df)} registros)")

    # Formatear tabla de inicio
    df_inicio = df.head(15).copy()
    if "Precio Operación" in df_inicio.columns:
        df_inicio["Precio Operación"] = df_inicio["Precio Operación"].apply(
            fmt
        )
    if "Valor Mercado" in df_inicio.columns:
        df_inicio["Valor Mercado"] = df_inicio["Valor Mercado"].apply(fmt)

    st.subheader("📋 Últimos Movimientos de la Liga")
    st.dataframe(df_inicio, hide_index=True, use_container_width=True)

# ==========================================
# PESTAÑA 2: MERCADO & SOBREPUJAS
# ==========================================
with tab_mercado:
    st.subheader("📊 Análisis Global de Mercado")

    df_mercado = df[
        (df["Vendedor"] == "Mercado")
        & (df["Tipo"] == "market")
        & (df["Precio Operación"] >= df["Valor Mercado"])
    ].copy()

    df_mercado["Sobreprecio (€)"] = (
        df_mercado["Precio Operación"] - df_mercado["Valor Mercado"]
    )
    df_mercado["Sobreprecio (%)"] = (
        df_mercado["Sobreprecio (€)"] / df_mercado["Valor Mercado"]
    ) * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pujas Mercado", f"{len(df_mercado)}")
    c2.metric("Sobrepuja Media Liga", f"+{df_mercado['Sobreprecio (%)'].mean():.1f}%")
    c3.metric(
        "Sobrepuja Mediana Liga", f"+{df_mercado['Sobreprecio (%)'].median():.1f}%"
    )

    st.divider()

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
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
    )
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# PESTAÑA 3: RIVALES & CLÁUSULAS
# ==========================================
with tab_rivales:
    todos_managers = set(df["Comprador"].unique()).union(set(df["Vendedor"].unique()))
    if "Mercado" in todos_managers:
        todos_managers.remove("Mercado")

    lista_rivales = sorted(list(todos_managers))
    rival_seleccionado = st.selectbox("🔍 Selecciona un Manager:", lista_rivales)

    # DATOS
    df_compras_mercado = df[
        (df["Comprador"] == rival_seleccionado)
        & (df["Vendedor"] == "Mercado")
        & (df["Tipo"] == "market")
        & (df["Precio Operación"] >= df["Valor Mercado"])
    ].copy()

    df_ventas = df[df["Vendedor"] == rival_seleccionado].copy()
    df_clausulas = df[
        (df["Comprador"] == rival_seleccionado) & (df["Tipo"] == "clauseIncrement")
    ].copy()
    df_robados = df[
        (df["Comprador"] == rival_seleccionado)
        & (df["Vendedor"] != "Mercado")
        & (df["Vendedor"] != rival_seleccionado)
    ].copy()
    df_perdidos = df[
        (df["Vendedor"] == rival_seleccionado)
        & (df["Comprador"] != "Mercado")
        & (df["Comprador"] != rival_seleccionado)
    ].copy()

    gasto_mercado = df_compras_mercado["Precio Operación"].sum()
    gasto_clausulas = df_clausulas["Precio Operación"].sum()
    gasto_robados = df_robados["Precio Operación"].sum()
    gasto_total_general = gasto_mercado + gasto_clausulas + gasto_robados

    ingreso_ventas = df_ventas["Precio Operación"].sum()
    balance_neto = ingreso_ventas - gasto_total_general

    # MÉTRICAS FINANCIERAS
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Gasto Total", fmt(gasto_total_general))
    m2.metric("Ingresos Ventas", fmt(ingreso_ventas))
    m3.metric(
        "Balance Neto",
        fmt(balance_neto),
        delta="Superávit" if balance_neto >= 0 else "Déficit",
    )

    if not df_compras_mercado.empty:
        df_compras_mercado["Sobreprecio (%)"] = (
            (
                df_compras_mercado["Precio Operación"]
                - df_compras_mercado["Valor Mercado"]
            )
            / df_compras_mercado["Valor Mercado"]
        ) * 100
        sobrepuja_media = df_compras_mercado["Sobreprecio (%)"].mean()
        m4.metric("Sobrepuja Media", f"+{sobrepuja_media:.1f}%")
    else:
        m4.metric("Sobrepuja Media", "0%")

    st.divider()

    # BLOQUE DE COMPRAS
    st.subheader(f"🛒 Pujas de Mercado ({len(df_compras_mercado)} fichajes)")

    if df_compras_mercado.empty:
        st.info("Sin fichajes directos de mercado.")
    else:
        fig_compras = px.bar(
            df_compras_mercado.nlargest(8, "Precio Operación"),
            x="Jugador",
            y="Precio Operación",
            text_auto=".2s",
            color="Sobreprecio (%)",
            color_continuous_scale="Reds",
        )
        fig_compras.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=280)
        st.plotly_chart(fig_compras, use_container_width=True)

        df_c_tabla = df_compras_mercado[
            [
                "Fecha",
                "Jugador",
                "Precio Operación",
                "Valor Mercado",
                "Sobreprecio (%)",
            ]
        ].copy()
        df_c_tabla["Precio Operación"] = df_c_tabla["Precio Operación"].apply(fmt)
        df_c_tabla["Valor Mercado"] = df_c_tabla["Valor Mercado"].apply(fmt)
        df_c_tabla["Sobreprecio (%)"] = df_c_tabla["Sobreprecio (%)"].apply(
            lambda x: f"+{x:.1f}%"
        )

        st.dataframe(df_c_tabla, hide_index=True, use_container_width=True)

    st.divider()

    # BLOQUE DE CLÁUSULAS Y ROBOS (En 2 Columnas para ahorrar espacio)
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader(f"🔒 Cláusulas Subidas ({len(df_clausulas)})")
        if df_clausulas.empty:
            st.caption("Sin subidas de cláusulas.")
        else:
            df_cl_tabla = df_clausulas[
                ["Fecha", "Jugador", "Precio Operación", "Valor Mercado"]
            ].copy()
            df_cl_tabla["Precio Operación"] = df_cl_tabla[
                "Precio Operación"
            ].apply(fmt)
            df_cl_tabla["Valor Mercado"] = df_cl_tabla["Valor Mercado"].apply(fmt)
            st.dataframe(
                df_cl_tabla.rename(columns={"Precio Operación": "Inversión"}),
                hide_index=True,
                use_container_width=True,
            )

    with col_right:
        st.subheader(f"⚡ Traspasos entre Rivales")
        if df_robados.empty and df_perdidos.empty:
            st.caption("Sin traspasos directos con rivales.")
        else:
            if not df_robados.empty:
                st.caption("🟢 Robados a otros:")
                df_r_tabla = df_robados[
                    ["Fecha", "Jugador", "Vendedor", "Precio Operación"]
                ].copy()
                df_r_tabla["Precio Operación"] = df_r_tabla[
                    "Precio Operación"
                ].apply(fmt)
                st.dataframe(
                    df_r_tabla, hide_index=True, use_container_width=True
                )

            if not df_perdidos.empty:
                st.caption("🔴 Vendidos / Perderá a otros:")
                df_p_tabla = df_perdidos[
                    ["Fecha", "Jugador", "Comprador", "Precio Operación"]
                ].copy()
                df_p_tabla["Precio Operación"] = df_p_tabla[
                    "Precio Operación"
                ].apply(fmt)
                st.dataframe(
                    df_p_tabla, hide_index=True, use_container_width=True
                )

    st.divider()

    # BLOQUE DE VENTAS
    st.subheader(f"💰 Ventas Realizadas ({len(df_ventas)})")
    if df_ventas.empty:
        st.info("Sin ventas registradas.")
    else:
        df_v_tabla = df_ventas[
            ["Fecha", "Jugador", "Comprador", "Precio Operación", "Tipo"]
        ].copy()
        df_v_tabla["Precio Operación"] = df_v_tabla["Precio Operación"].apply(fmt)
        st.dataframe(df_v_tabla, hide_index=True, use_container_width=True)
