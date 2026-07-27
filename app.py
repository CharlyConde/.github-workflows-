import os
import re
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen

import pandas as pd
import plotly.express as px
import streamlit as st

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Conde News | Biwenger Panel",
    page_icon="🧛‍♂️",
    layout="wide",
)

# ==========================================
# CONFIGURACIÓN Y ESTILOS CSS
# ==========================================
st.markdown(
    """
    <style>
    /* Estilo base para botones de leyenda y componentes */
    .leyenda-item, div[data-testid="stHorizontalBlock"] button {
        color: #000000 !important;             /* Texto negro puro */
        font-weight: 600 !important;            /* Texto seminegrita para mejor lectura */
        opacity: 1 !important;                  /* Quita la transparencia/lavado */
        filter: none !important;                /* Elimina efectos de brillo o desenfoque */
        border: none !important;                /* Quita bordes transparentes */
        box-shadow: none !important;            /* Quita sombras o resplandores */
    }

    /* Colores por tipo de operación */
    .btn-compra    { background-color: #4A90E2 !important; } /* Azul */
    .btn-venta     { background-color: #50E3C2 !important; } /* Verde */
    .btn-subida    { background-color: #BD10E0 !important; } /* Morado */
    .btn-subasta   { background-color: #F5A623 !important; } /* Naranja */
    .btn-clausula  { background-color: #E35070 !important; } /* Rosa / Rojo */

    /* Estilo para el contenedor del título principal con el logo de Biwenger */
    .header-container {
        display: flex;
        align-items: center;
        gap: 18px;
        margin-bottom: 20px;
    }
    .header-logo {
        height: 65px;
        width: auto;
    }
    .header-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.2;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Configuración por defecto de Plotly para desactivar la barra de herramientas
PLOTLY_CONFIG = {"displayModeBar": False}


# ==========================================
# FUNCIONES AUXILIARES DE FORMATO
# ==========================================
def fmt(val):
    """Formato financiero con 1 decimal y formato español: 12.345.678,0 €"""
    if pd.isna(val) or val is None:
        return "-"
    return f"{val:,.1f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(val):
    """Formato porcentaje con 1 decimal y formato español: +12,5%"""
    if pd.isna(val) or val is None:
        return "-"
    signo = "+" if val > 0 else ""
    return f"{signo}{val:,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def color_rows(row):
    """Colorea filas según el tipo de operación para DataFrames de Pandas."""
    tipo = row.get("🏷️ Tipo", row.get("Tipo", ""))
    vendedor = row.get("🏪 Vendedor", row.get("Vendedor", ""))
    comprador = row.get("🛒 Comprador", row.get("Comprador", ""))
    precio = row.get("_Precio_Num", 0)
    vm = row.get("_VM_Num", 0)

    # 1. Compra a Mercado
    if tipo == "market" and vendedor == "Mercado":
        return ["background-color: #e6f0fa; color: #0f3460;"] * len(row)

    # 2. Venta a Mercado
    elif tipo == "transfer" and comprador == "Mercado":
        return ["background-color: #e6ffe6; color: #1b5e20;"] * len(row)

    # 3. Subida de Cláusula
    elif tipo == "clauseIncrement":
        return ["background-color: #f3e8ff; color: #4a154b;"] * len(row)

    # 4. Traspaso entre Managers (Clausulazo vs Subasta/Acuerdo)
    elif vendedor != "Mercado" and comprador != "Mercado":
        if precio <= vm or abs(precio - vm) < 1000:
            return [
                "background-color: #ffebee; color: #b71c1c; font-weight: bold;"
            ] * len(row)
        else:
            return ["background-color: #fff3e0; color: #e65100;"] * len(row)

    return [""] * len(row)


@st.cache_data(ttl=1800)
def fetch_rss_news():
    """Obtiene y limpia noticias RSS de fútbol."""
    urls = [
        "https://e00-marca.uecdn.es/rss/futbol/primera-division.xml",
        "https://as.com/rss/futbol/primera.xml",
    ]
    noticias = []

    for url in urls:
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            html = urlopen(req).read()
            root = ET.fromstring(html)

            for item in root.findall("./channel/item"):
                title = (
                    item.find("title").text if item.find("title") is not None else ""
                )
                link = (
                    item.find("link").text if item.find("link") is not None else ""
                )
                desc = (
                    item.find("description").text
                    if item.find("description") is not None
                    else "Sin descripción disponible."
                )
                pubDate = (
                    item.find("pubDate").text
                    if item.find("pubDate") is not None
                    else ""
                )

                desc_clean = (
                    desc.replace("<p>", "")
                    .replace("</p>", "")
                    .replace("<br>", "\n")
                )
                if "<" in desc_clean and ">" in desc_clean:
                    desc_clean = re.sub("<[^<]+?>", "", desc_clean)

                if title:
                    noticias.append(
                        {
                            "Título": title,
                            "Resumen": desc_clean.strip(),
                            "Fecha": pubDate,
                            "Enlace": link,
                        }
                    )
        except Exception:
            continue

    return noticias


@st.cache_data(ttl=300)
def load_data():
    """Carga de datos con caché desde CSV o XLSX."""
    csv_file = "historial_biwenger_completo.csv"
    xlsx_file = "historial_biwenger_completo.xlsx"

    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)
    elif os.path.exists(xlsx_file):
        return pd.read_excel(xlsx_file)
    return None


# ==========================================
# APLICACIÓN PRINCIPAL
# ==========================================
df = load_data()

# --- HEADER PERSONALIZADO (LOGO OFICIAL BIWENGER + CONDE NEWS) ---
st.markdown(
    """
    <div class="header-container">
        <img src="https://biwenger.com/assets/images/logo.png" class="header-logo" alt="Biwenger Logo">
        <div>
            <div class="header-title">🧛‍♂️ ¡Bienvenidos a la mejor liga del mundo! Y al mejor análisis del mundo, ¡Conde News!</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if df is None or df.empty:
    st.info("Cargando datos o esperando primera actualización...")
    st.stop()

# --- PESTAÑAS DE NAVEGACIÓN ---
tab_inicio, tab_kpis, tab_mercado, tab_rivales, tab_noticias = st.tabs(
    [
        "📋 Histórico Completo",
        "🏆 Récords & KPIs",
        "📊 Mercado & Pujas",
        "👥 Rivales & Cláusulas",
        "📰 Noticias LaLiga",
    ]
)

# ==========================================
# PESTAÑA 1: HISTÓRICO COMPLETO
# ==========================================
with tab_inicio:
    st.caption(f"Mostrando el histórico de {len(df)} registros procesados.")

    st.markdown(
        """
        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; font-size: 0.85rem;">
            <span style="background-color: #e6f0fa; color: #0f3460; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟦 Compra Mercado</span>
            <span style="background-color: #e6ffe6; color: #1b5e20; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟩 Venta Mercado</span>
            <span style="background-color: #f3e8ff; color: #4a154b; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟪 Subida Cláusula</span>
            <span style="background-color: #fff3e0; color: #e65100; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟧 Subasta / Acuerdo Rival</span>
            <span style="background-color: #ffebee; color: #b71c1c; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟥 Clausulazo Rival</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_inicio = df.copy()

    df_inicio["_Precio_Num"] = df_inicio["Precio Operación"]
    df_inicio["_VM_Num"] = df_inicio["Valor Mercado"]

    df_inicio["Sobreprecio (€)"] = (
        df_inicio["Precio Operación"] - df_inicio["Valor Mercado"]
    )
    df_inicio["Sobreprecio (%)"] = (
        df_inicio["Sobreprecio (€)"]
        / df_inicio["Valor Mercado"].replace(0, 1)
    ) * 100

    df_inicio_formatted = df_inicio.copy()
    df_inicio_formatted["Precio Operación"] = df_inicio_formatted[
        "Precio Operación"
    ].apply(fmt)
    df_inicio_formatted["Valor Mercado"] = df_inicio_formatted[
        "Valor Mercado"
    ].apply(fmt)
    df_inicio_formatted["Sobreprecio (€)"] = df_inicio_formatted[
        "Sobreprecio (€)"
    ].apply(fmt)
    df_inicio_formatted["Sobreprecio (%)"] = df_inicio_formatted[
        "Sobreprecio (%)"
    ].apply(fmt_pct)

    column_map = {
        "Fecha": "📅 Fecha",
        "Jugador": "👤 Jugador",
        "Vendedor": "🏪 Vendedor",
        "Comprador": "🛒 Comprador",
        "Precio Operación": "💰 Precio Operación",
        "Valor Mercado": "📈 Valor Mercado",
        "Sobreprecio (€)": "➕ Sobreprecio (€)",
        "Sobreprecio (%)": "📊 Sobreprecio (%)",
        "Tipo": "🏷️ Tipo",
    }

    df_inicio_formatted = df_inicio_formatted.rename(columns=column_map)

    cols_mostrar = list(column_map.values())
    df_styled = df_inicio_formatted[
        cols_mostrar + ["_Precio_Num", "_VM_Num"]
    ].style.apply(color_rows, axis=1)

    st.dataframe(
        df_styled,
        column_order=cols_mostrar,
        hide_index=True,
        use_container_width=True,
        height=730,
    )

# ==========================================
# PESTAÑA 2: RÉCORDS & KPIS (HALL OF FAME)
# ==========================================
with tab_kpis:
    st.subheader("🏆 Hall of Fame y Datos Destacados de la Liga")

    df_pujas_mercado = df[
        (df["Vendedor"] == "Mercado")
        & (df["Tipo"] == "market")
        & (df["Precio Operación"] >= df["Valor Mercado"])
    ].copy()

    df_pujas_mercado["Sobreprecio (€)"] = (
        df_pujas_mercado["Precio Operación"] - df_pujas_mercado["Valor Mercado"]
    )
    df_pujas_mercado["Sobreprecio (%)"] = (
        df_pujas_mercado["Sobreprecio (€)"] / df_pujas_mercado["Valor Mercado"]
    ) * 100

    if not df_pujas_mercado.empty:
        top_puja = df_pujas_mercado.loc[df_pujas_mercado["Precio Operación"].idxmax()]
        top_locura_pct = df_pujas_mercado.loc[df_pujas_mercado["Sobreprecio (%)"].idxmax()]
    else:
        top_puja = top_locura_pct = None

    df_entre_rivales = df[
        (df["Vendedor"] != "Mercado")
        & (df["Comprador"] != "Mercado")
        & (df["Vendedor"] != df["Comprador"])
    ]
    if not df_entre_rivales.empty:
        top_traspaso = df_entre_rivales.loc[df_entre_rivales["Precio Operación"].idxmax()]
    else:
        top_traspaso = None

    df_clau_all = df[df["Tipo"] == "clauseIncrement"]
    if not df_clau_all.empty:
        top_clau = df_clau_all.loc[df_clau_all["Precio Operación"].idxmax()]
    else:
        top_clau = None

    k1, k2, k3, k4 = st.columns(4)

    if top_puja is not None:
        k1.metric("🎯 Mayor Puja Mercado", fmt(top_puja["Precio Operación"]), f"{top_puja['Jugador']}")

    if top_locura_pct is not None:
        k2.metric("🚀 Mayor Sobrepuja (%)", fmt_pct(top_locura_pct["Sobreprecio (%)"]), f"{top_locura_pct['Jugador']}")

    if top_traspaso is not None:
        k3.metric("⚡ Mayor Traspaso", fmt(top_traspaso["Precio Operación"]), f"{top_traspaso['Jugador']}")
    else:
        k3.metric("⚡ Mayor Traspaso", "Sin datos", "Sin registros")

    if top_clau is not None:
        k4.metric("🔒 Mayor Subida Cláusula", fmt(top_clau["Precio Operación"]), f"{top_clau['Jugador']}")

    st.divider()

    # --- CÁLCULO DE DINERO EN CAJA (PRESUPUESTO INICIAL = 45M€) ---
    PRESUPUESTO_INICIAL = 45_000_000

    df_gastos_tot = (
        df[df["Comprador"] != "Mercado"]
        .groupby("Comprador")["Precio Operación"]
        .sum()
        .reset_index()
    )
    df_gastos_tot.columns = ["Manager", "GastoTotal"]

    df_ventas_tot = (
        df[df["Vendedor"] != "Mercado"]
        .groupby("Vendedor")["Precio Operación"]
        .sum()
        .reset_index()
    )
    df_ventas_tot.columns = ["Manager", "IngresoTotal"]

    df_caja = pd.merge(df_gastos_tot, df_ventas_tot, on="Manager", how="outer").fillna(0)
    df_caja["Caja_Estimada"] = PRESUPUESTO_INICIAL + df_caja["IngresoTotal"] - df_caja["GastoTotal"]
    df_caja = df_caja.sort_values(by="Caja_Estimada", ascending=False)
    
    df_caja["Caja_Fmt"] = df_caja["Caja_Estimada"].apply(fmt)

    # --- GRÁFICO 1: DINERO EN CAJA ---
    st.subheader("💵 Dinero en Caja Estimado (Base 45M€)")
    fig_caja = px.bar(
        df_caja,
        x="Caja_Estimada",
        y="Manager",
        orientation="h",
        color="Caja_Estimada",
        color_continuous_scale="Greens",
        custom_data=["Caja_Fmt"],
    )
    fig_caja.update_traces(
        texttemplate="%{customdata[0]}",
        textposition="outside",
        hovertemplate="<b>Manager:</b> %{y}<br><b>Dinero en Caja:</b> %{customdata[0]}<extra></extra>",
    )
    fig_caja.update_layout(
        yaxis={"categoryorder": "total ascending", "title": ""},
        xaxis={"title": "Euros (€)"},
        coloraxis_showscale=False,
        height=450,
        margin=dict(l=20, r=50, t=20, b=20),
    )
    st.plotly_chart(fig_caja, use_container_width=True, config=PLOTLY_CONFIG)

    st.divider()

    # --- GRÁFICO 2: SOBREPUJADORES MEDIOS ---
    st.subheader("🔥 Sobrepujadores (% Medio)")
    if not df_pujas_mercado.empty:
        df_rank_pujas = (
            df_pujas_mercado.groupby("Comprador")["Sobreprecio (%)"]
            .mean()
            .reset_index()
            .sort_values(by="Sobreprecio (%)", ascending=False)
        )
        df_rank_pujas["Pct_Fmt"] = df_rank_pujas["Sobreprecio (%)"].apply(fmt_pct)

        fig_rank1 = px.bar(
            df_rank_pujas,
            x="Sobreprecio (%)",
            y="Comprador",
            orientation="h",
            color="Sobreprecio (%)",
            color_continuous_scale="Reds",
            custom_data=["Pct_Fmt"],
        )
        fig_rank1.update_traces(
            texttemplate="%{customdata[0]}",
            textposition="outside",
            hovertemplate="<b>Manager:</b> %{y}<br><b>Sobrepuja Media:</b> %{customdata[0]}<extra></extra>",
        )
        fig_rank1.update_layout(
            yaxis={"categoryorder": "total ascending", "title": ""},
            xaxis={"title": "% Sobrepuja"},
            coloraxis_showscale=False,
            height=450,
            margin=dict(l=20, r=50, t=20, b=20),
        )
        st.plotly_chart(fig_rank1, use_container_width=True, config=PLOTLY_CONFIG)

    st.divider()

    # --- GRÁFICO 3: INVERSIÓN TOTAL ---
    st.subheader("💰 Inversión Total por Mánager")
    df_gastos = (
        df.groupby("Comprador")["Precio Operación"].sum().reset_index()
    )
    df_gastos = df_gastos[df_gastos["Comprador"] != "Mercado"].sort_values(
        by="Precio Operación", ascending=False
    )
    df_gastos["Inversion_Fmt"] = df_gastos["Precio Operación"].apply(fmt)

    fig_rank2 = px.bar(
        df_gastos,
        x="Precio Operación",
        y="Comprador",
        orientation="h",
        color="Precio Operación",
        color_continuous_scale="Blues",
        custom_data=["Inversion_Fmt"],
    )
    fig_rank2.update_traces(
        texttemplate="%{customdata[0]}",
        textposition="outside",
        hovertemplate="<b>Manager:</b> %{y}<br><b>Inversión Total:</b> %{customdata[0]}<extra></extra>",
    )
    fig_rank2.update_layout(
        yaxis={"categoryorder": "total ascending", "title": ""},
        xaxis={"title": "Gasto Total (€)"},
        coloraxis_showscale=False,
        height=450,
        margin=dict(l=20, r=50, t=20, b=20),
    )
    st.plotly_chart(fig_rank2, use_container_width=True, config=PLOTLY_CONFIG)

# ==========================================
# PESTAÑA 3: MERCADO & SOBREPUJAS
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
    c2.metric("Sobrepuja Media Liga", fmt_pct(df_mercado["Sobreprecio (%)"].mean()))
    c3.metric("Sobrepuja Mediana Liga", fmt_pct(df_mercado["Sobreprecio (%)"].median()))

    st.divider()

    st.subheader("🔥 Top 10 Fichajes Más Caros del Mercado")
    top10 = df_mercado.nlargest(10, "Precio Operación").copy()
    top10["Precio_Fmt"] = top10["Precio Operación"].apply(fmt)

    fig = px.bar(
        top10,
        x="Precio Operación",
        y="Jugador",
        color="Comprador",
        orientation="h",
        custom_data=["Precio_Fmt", "Comprador"],
    )
    fig.update_traces(
        texttemplate="%{customdata[0]}",
        textposition="outside",
        hovertemplate="<b>Jugador:</b> %{y}<br><b>Comprador:</b> %{customdata[1]}<br><b>Precio:</b> %{customdata[0]}<extra></extra>",
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending", "title": ""},
        xaxis={"title": "Precio (€)"},
        margin=dict(l=20, r=50, t=20, b=20),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

# ==========================================
# PESTAÑA 4: RIVALES & CLÁUSULAS
# ==========================================
with tab_rivales:
    todos_managers = set(df["Comprador"].unique()).union(set(df["Vendedor"].unique()))
    if "Mercado" in todos_managers:
        todos_managers.remove("Mercado")

    lista_rivales = sorted(list(todos_managers))
    rival_seleccionado = st.selectbox("🔍 Selecciona un Manager:", lista_rivales)

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
        m4.metric("Sobrepuja Media", fmt_pct(sobrepuja_media))
    else:
        m4.metric("Sobrepuja Media", "0,0%")

    st.divider()

    st.subheader(f"🛒 Pujas de Mercado ({len(df_compras_mercado)} fichajes)")

    if df_compras_mercado.empty:
        st.info("Sin fichajes directos de mercado.")
    else:
        top_compras_rival = df_compras_mercado.nlargest(8, "Precio Operación").copy()
        top_compras_rival["Precio_Fmt"] = top_compras_rival["Precio Operación"].apply(fmt)
        top_compras_rival["Sobreprecio_Fmt"] = top_compras_rival["Sobreprecio (%)"].apply(fmt_pct)

        fig_compras = px.bar(
            top_compras_rival,
            x="Jugador",
            y="Precio Operación",
            color="Sobreprecio (%)",
            color_continuous_scale="Reds",
            custom_data=["Precio_Fmt", "Sobreprecio_Fmt"],
        )
        fig_compras.update_traces(
            texttemplate="%{customdata[0]}",
            textposition="outside",
            hovertemplate="<b>Jugador:</b> %{x}<br><b>Precio:</b> %{customdata[0]}<br><b>Sobrepuja:</b> %{customdata[1]}<extra></extra>",
        )
        fig_compras.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=340)
        st.plotly_chart(fig_compras, use_container_width=True, config=PLOTLY_CONFIG)

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
        df_c_tabla["Sobreprecio (%)"] = df_c_tabla["Sobreprecio (%)"].apply(fmt_pct)

        st.dataframe(
            df_c_tabla.rename(
                columns={
                    "Fecha": "📅 Fecha",
                    "Jugador": "👤 Jugador",
                    "Precio Operación": "💰 Precio",
                    "Valor Mercado": "📈 VM",
                    "Sobreprecio (%)": "📊 sobrepuja",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

    st.divider()

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
                df_cl_tabla.rename(
                    columns={
                        "Fecha": "📅 Fecha",
                        "Jugador": "👤 Jugador",
                        "Precio Operación": "🔒 Inversión",
                        "Valor Mercado": "📈 VM",
                    }
                ),
                hide_index=True,
                use_container_width=True,
            )

    with col_right:
        st.subheader("⚡ Traspasos entre Rivales")
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
                    df_r_tabla.rename(
                        columns={
                            "Fecha": "📅 Fecha",
                            "Jugador": "👤 Jugador",
                            "Vendedor": "🏪 Víctima",
                            "Precio Operación": "💰 Precio",
                        }
                    ),
                    hide_index=True,
                    use_container_width=True,
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
                    df_p_tabla.rename(
                        columns={
                            "Fecha": "📅 Fecha",
                            "Jugador": "👤 Jugador",
                            "Comprador": "🛒 Comprador",
                            "Precio Operación": "💰 Precio",
                        }
                    ),
                    hide_index=True,
                    use_container_width=True,
                )

    st.divider()

    st.subheader(f"💰 Ventas Realizadas ({len(df_ventas)})")
    if df_ventas.empty:
        st.info("Sin ventas registradas.")
    else:
        df_v_tabla = df_ventas[
            ["Fecha", "Jugador", "Comprador", "Precio Operación", "Tipo"]
        ].copy()
        df_v_tabla["Precio Operación"] = df_v_tabla["Precio Operación"].apply(fmt)
        st.dataframe(
            df_v_tabla.rename(
                columns={
                    "Fecha": "📅 Fecha",
                    "Jugador": "👤 Jugador",
                    "Comprador": "🛒 Comprador",
                    "Precio Operación": "💰 Precio",
                    "Tipo": "🏷️ Tipo",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

# ==========================================
# PESTAÑA 5: NOTICIAS LALIGA
# ==========================================
with tab_noticias:
    st.subheader("📰 Noticias LaLiga & Rumores de Fichajes")
    st.caption(
        "Titulares en tiempo real. Haz clic en cualquier noticia para leer el resumen desplegable."
    )

    noticias = fetch_rss_news()

    if not noticias:
        st.warning("No se han podido cargar las noticias en este momento.")
    else:
        busqueda = st.text_input(
            "🔍 Buscar jugador o equipo en noticias:",
            placeholder="Ej: Mbappe, Williams, Betis...",
        )

        noticias_filtradas = [
            n
            for n in noticias
            if busqueda.lower() in n["Título"].lower()
            or busqueda.lower() in n["Resumen"].lower()
        ]

        st.write(f"Mostrando {len(noticias_filtradas)} noticias:")

        for noticia in noticias_filtradas[:25]:
            with st.expander(f"📌 {noticia['Título']}"):
                if noticia["Fecha"]:
                    st.caption(f"🗓️ {noticia['Fecha']}")
                st.write(noticia["Resumen"])
                if noticia["Enlace"]:
                    st.markdown(
                        f"[🔗 Leer noticia completa en la web]({noticia['Enlace']})"
                    )
