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
st.caption("Análisis en tiempo real de sobrepujas, fichajes, cláusulas y balance.")

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
    st.success(f"¡Datos cargados con éxito! ({len(df)} registros)")

    # Tabla Resumen Últimos Movimientos
    st.subheader("📋 Últimos Movimientos de la Liga")
    st.dataframe(df.head(10), hide_index=True, use_container_width=True)

# ==========================================
# PESTAÑA 2: MERCADO & SOBREPUJAS
# ==========================================
with tab_mercado:
    st.header("📊 Análisis Global de Mercado")

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

    # Métricas adaptadas
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pujas de Mercado", f"{len(df_mercado)}")
    c2.metric("Sobrepuja Media Liga", f"+{df_mercado['Sobreprecio (%)'].mean():.1f}%")
    c3.metric(
        "Sobrepuja Mediana Liga", f"+{df_mercado['Sobreprecio (%)'].median():.1f}%"
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
# PESTAÑA 3: RIVALES & CLÁUSULAS
# ==========================================
with tab_rivales:
    st.header("👥 Análisis 360º por Manager")

    # Obtener lista única de managers (compradores y vendedores)
    todos_managers = set(df["Comprador"].unique()).union(set(df["Vendedor"].unique()))
    if "Mercado" in todos_managers:
        todos_managers.remove("Mercado")

    lista_rivales = sorted(list(todos_managers))
    rival_seleccionado = st.selectbox("🔍 Selecciona un Manager:", lista_rivales)

    st.divider()

    # --- 0. BALANCE FINANCIERO Y RESUMEN GENERAL ---
    # Compras de Mercado Puras
    df_compras_mercado = df[
        (df["Comprador"] == rival_seleccionado)
        & (df["Vendedor"] == "Mercado")
        & (df["Tipo"] == "market")
        & (df["Precio Operación"] >= df["Valor Mercado"])
    ].copy()

    # Ventas totales realizadas
    df_ventas = df[df["Vendedor"] == rival_seleccionado].copy()

    # Inversión en Cláusulas
    df_clausulas = df[
        (df["Comprador"] == rival_seleccionado) & (df["Tipo"] == "clauseIncrement")
    ].copy()

    # Clausulazos robados a rivales (Compra directa a otro manager)
    df_robados = df[
        (df["Comprador"] == rival_seleccionado)
        & (df["Vendedor"] != "Mercado")
        & (df["Vendedor"] != rival_seleccionado)
    ].copy()

    # Clausulazos recibidos / perdidos (Venta directa a otro manager)
    df_perdidos = df[
        (df["Vendedor"] == rival_seleccionado)
        & (df["Comprador"] != "Mercado")
        & (df["Comprador"] != rival_seleccionado)
    ].copy()

    # Cálculos Financieros
    gasto_mercado = df_compras_mercado["Precio Operación"].sum()
    gasto_clausulas = df_clausulas["Precio Operación"].sum()
    gasto_robados = df_robados["Precio Operación"].sum()
    gasto_total_general = gasto_mercado + gasto_clausulas + gasto_robados

    ingreso_ventas = df_ventas["Precio Operación"].sum()
    balance_neto = ingreso_ventas - gasto_total_general

    # MÉTRES PRINCIPALES DEL BALANCE
    st.subheader("💳 Balance Financiero")
    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Gasto Total Acumulado", f"{gasto_total_general:,.0f} €")
    m2.metric("Ingresos por Ventas", f"{ingreso_ventas:,.0f} €")
    m3.metric(
        "Balance Neto (€)",
        f"{balance_neto:,.0f} €",
        delta="Superávit" if balance_neto >= 0 else "Déficit",
    )

    # Sobrepuja Media Real
    if not df_compras_mercado.empty:
        df_compras_mercado["Sobreprecio (%)"] = (
            (
                df_compras_mercado["Precio Operación"]
                - df_compras_mercado["Valor Mercado"]
            )
            / df_compras_mercado["Valor Mercado"]
        ) * 100
        sobrepuja_media = df_compras_mercado["Sobreprecio (%)"].mean()
        m4.metric("Sobrepuja Media Mercado", f"+{sobrepuja_media:.1f}%")
    else:
        m4.metric("Sobrepuja Media Mercado", "0%")

    st.divider()

    # --- SECCIÓN A: PUJAS DE MERCADO ---
    st.subheader(f"🛒 Pujas de Mercado ({len(df_compras_mercado)} fichajes)")

    if df_compras_mercado.empty:
        st.info("No hay fichajes directos de mercado registrados para este manager.")
    else:
        fig_compras = px.bar(
            df_compras_mercado.nlargest(8, "Precio Operación"),
            x="Jugador",
            y="Precio Operación",
            text_auto=".2s",
            color="Sobreprecio (%)",
            color_continuous_scale="Reds",
            title=f"Principales Pujas de {rival_seleccionado}",
        )
        fig_compras.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320)
        st.plotly_chart(fig_compras, use_container_width=True)

        st.dataframe(
            df_compras_mercado[
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

    # --- SECCIÓN B: SUBIDAS DE CLÁUSULAS ---
    st.subheader(f"🔒 Inversión en Cláusulas ({len(df_clausulas)} subidas)")

    if df_clausulas.empty:
        st.info("Este manager no ha realizado subidas de cláusulas registradas.")
    else:
        c_clau1, c_clau2 = st.columns(2)
        c_clau1.metric("Gasto Total en Blindajes", f"{gasto_clausulas:,.0f} €")
        c_clau2.metric("Nº Jugadores Subidos", f"{len(df_clausulas)}")

        st.dataframe(
            df_clausulas[
                ["Fecha", "Jugador", "Precio Operación", "Valor Mercado"]
            ].rename(columns={"Precio Operación": "Inversión Cláusula"}),
            hide_index=True,
            use_container_width=True,
        )

    st.divider()

    # --- SECCIÓN C: CLAUSULAZOS Y TRASPASOS ENTRE RIVALES ---
    col_rob, col_perd = st.columns(2)

    with col_rob:
        st.subheader(f"⚡ Robados a Rivales ({len(df_robados)})")
        if df_robados.empty:
            st.caption("No ha robado jugadores a otros managers.")
        else:
            st.dataframe(
                df_robados[
                    ["Fecha", "Jugador", "Vendedor", "Precio Operación"]
                ].rename(columns={"Vendedor": "Victima"}),
                hide_index=True,
                use_container_width=True,
            )

    with col_perd:
        st.subheader(f"🚨 Perdedores / Ventas a Rivales ({len(df_perdidos)})")
        if df_perdidos.empty:
            st.caption("No le han robado ni ha vendido a otros managers.")
        else:
            st.dataframe(
                df_perdidos[
                    ["Fecha", "Jugador", "Comprador", "Precio Operación"]
                ].rename(columns={"Comprador": "Comprador Rival"}),
                hide_index=True,
                use_container_width=True,
            )

    st.divider()

    # --- SECCIÓN D: VENTAS REALIZADAS ---
    st.subheader(f"💰 Histórico de Ventas ({len(df_ventas)})")

    if df_ventas.empty:
        st.info("Este manager aún no ha realizado ventas.")
    else:
        st.dataframe(
            df_ventas[
                ["Fecha", "Jugador", "Comprador", "Precio Operación", "Tipo"]
            ],
            hide_index=True,
            use_container_width=True,
        )
