import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de la página web (Título y layout ancho)
st.set_page_config(
    page_title="Liga Biwenger - Stats & Finanzas",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Panel Financiero & Mercado Biwenger")
st.markdown("Análisis en tiempo real de sobrepujas, fichajes y presupuestos.")


# Cargar los datos desde el CSV generado por tu script
@st.cache_data(ttl=600)  # Recarga datos automáticamente cada 10 min
def cargar_datos():
    url_csv = "https://raw.githubusercontent.com/TU_USUARIO/TU_REPOSITORIO/main/historial_biwenger_completo.csv"
    df = pd.read_csv(url_csv)
    return df


try:
    df = cargar_datos()

    # --- METRICAS PRINCIPALES (TARJETAS TOP) ---
    col1, col2, col3, col4 = st.columns(4)

    total_movimientos = len(df)
    gasto_total = df['Precio Operación'].sum()
    fichaje_top = df.loc[df['Precio Operación'].idxmax()]
    sobrepuja_top = df.loc[df['Sobreprecio (€)'].idxmax()]

    col1.metric("Total Operaciones", f"{total_movimientos}")
    col2.metric("Gasto Total Liga", f"{gasto_total:,.0f} €")
    col3.metric(
        "Fichaje más Caro",
        f"{fichaje_top['Jugador']}",
        f"{fichaje_top['Precio Operación']:,.0f} €",
    )
    col4.metric(
        "Mayor Sobrepuja",
        f"{sobrepuja_top['Jugador']}",
        f"+{sobrepuja_top['Sobreprecio (€)']:,.0f} €",
    )

    st.divider()

    # --- PESTAÑAS NAVEGABLES ---
    tab1, tab2, tab3 = st.tabs(
        ["📊 Gráficos de Gasto", "🔥 Top Sobrepujas", "👤 Por Manager"]
    )

    with tab1:
        st.subheader("Gasto Acumulado por Manager")
        # Sumamos cuánto ha gastado cada comprador
        gasto_manager = (
            df.groupby("Comprador")["Precio Operación"].sum().reset_index()
        )

        fig_gasto = px.bar(
            gasto_manager,
            x="Comprador",
            y="Precio Operación",
            color="Comprador",
            title="Inversión Total en Mercado/Fichajes (€)",
            text_auto=".2s",
        )
        st.plotly_chart(fig_gasto, use_container_width=True)

    with tab2:
        st.subheader("Tabla de Fichajes y Sobrepujas")
        # Filtro interactivo por manager
        managers = ["Todos"] + list(df["Comprador"].unique())
        selected_manager = st.selectbox("Filtrar por Comprador:", managers)

        if selected_manager != "Todos":
            df_filtered = df[df["Comprador"] == selected_manager]
        else:
            df_filtered = df

        # Mostramos la tabla formateada y ejecutable en web
        st.dataframe(
            df_filtered[[
                "Fecha",
                "Jugador",
                "Comprador",
                "Vendedor",
                "Precio Operación",
                "Valor Mercado",
                "Sobreprecio (€)",
                "Sobreprecio (%)",
            ]],
            use_container_width=True,
            hide_index=True,
        )

    with tab3:
        st.subheader("Perfil Financiero Individual")
        m_select = st.selectbox(
            "Selecciona Manager:", df["Comprador"].unique()
        )

        compras_m = df[df["Comprador"] == m_select]
        ventas_m = df[df["Vendedor"] == m_select]

        c_col1, c_col2 = st.columns(2)
        with c_col1:
            st.write(f"**Compras realizadas:** {len(compras_m)}")
            st.write(
                f"**Gasto total:** {compras_m['Precio Operación'].sum():,.0f} €"
            )
            st.write(
                "**Sobreprecio medio pagado:**"
                f" {compras_m['Sobreprecio (%)'].mean():.1f}%"
            )

        with c_col2:
            st.write(f"**Ventas realizadas:** {len(ventas_m)}")
            st.write(
                "**Ingresos totales por ventas:**"
                f" {ventas_m['Precio Operación'].sum():,.0f} €"
            )

except Exception as e:
    st.info("Cargando datos o esperando primera actualización del CSV...")
