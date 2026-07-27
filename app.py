import os
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen

import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Configuración de la página
st.set_page_config(
    page_title="Biwenger Stats & Mercado", page_icon="⚽", layout="wide"
)

# 2. CSS personalizado avanzadado con fondos suaves por temática
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1rem !important;
        }
        h1 { font-size: 1.8rem !important; padding-bottom: 0rem !important; }
        h2, h3 { font-size: 1.2rem !important; margin-top: 0.5rem !important; margin-bottom: 0.5rem !important; }
        hr { margin-top: 0.8rem !important; margin-bottom: 0.8rem !important; }
        
        /* Estilo elegante para las métricas */
        [data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 10px 15px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Diseños de fondo suave para las pestañas */
        div[data-baseweb="tab-panel"]:nth-child(2) {
            background: linear-gradient(rgba(255,255,255,0.96), rgba(255,255,255,0.96)), 
                        url("https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1200&q=80");
            background-size: cover;
        }
        div[data-baseweb="tab-panel"]:nth-child(3) {
            background: linear-gradient(rgba(255,255,255,0.95), rgba(255,255,255,0.95)), 
                        url("https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=1200&q=80");
            background-size: cover;
        }
        div[data-baseweb="tab-panel"]:nth-child(4) {
            background: linear-gradient(rgba(255,255,255,0.95), rgba(255,255,255,0.95)), 
                        url("https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1200&q=80");
            background-size: cover;
        }
    </style>
""",
    unsafe_allow_html=True,
)


# Formato financiero en euros (€) con separadores de miles
def fmt(val):
    if pd.isna(val) or val is None:
        return "-"
    return f"{val:,.0f} €".replace(",", "X").replace(".", ",").replace("X", ".")


# Función para colorear filas según el tipo de operación
def color_rows(row):
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


# Función para obtener noticias RSS
@st.cache_data(ttl=1800)
def fetch_rss_news():
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
                    import re

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
    ].apply(lambda x: f"+{x:.1f}%" if x > 0 else f"{x:.1f}%")

    # Mapeo de columnas con Iconos
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
        top_puja = df_pujas_mercado.loc[
            df_pujas_mercado["Precio Operación"].idxmax()
        ]
        top_locura_pct = df_pujas_mercado.loc[
            df_pujas_mercado["Sobreprecio (%)"].idxmax()
        ]
    else:
        top_puja = top_locura_pct = None

    df_entre_rivales = df[
        (df["Vendedor"] != "Mercado")
        & (df["Comprador"] != "Mercado")
        & (df["Vendedor"] != df["Comprador"])
    ]
    if not df_entre_rivales.empty:
        top_traspaso = df_entre_rivales.loc[
            df_entre_rivales["Precio Operación"].idxmax()
        ]
    else:
        top_traspaso = None

    df_clau_all = df[df["Tipo"] == "clauseIncrement"]
    if not df_clau_all.empty:
        top_clau = df_clau_all.loc[df_clau_all["Precio Operación"].idxmax()]
    else:
        top_clau = None

    k1, k2, k3, k4 = st.columns(4)

    if top_puja is not None:
        k1.metric(
            "🎯 Mayor Puja al Mercado",
            fmt(top_puja["Precio Operación"]),
            f"{top_puja['Jugador']} ({top_puja['Comprador']})",
        )

    if top_locura_pct is not None:
        k2.metric(
            "🚀 Mayor Sobrepuja (%)",
            f"+{top_locura_pct['Sobreprecio (%)']:.1f}%",
            f"{top_locura_pct['Jugador']} ({top_locura_pct['Comprador']})",
        )

    if top_traspaso is not None:
        k3.metric(
            "⚡ Mayor Clausulazo / Traspaso",
            fmt(top_traspaso["Precio Operación"]),
            f"{top_traspaso['Jugador']} ({top_traspaso['Vendedor']} ➡️ {top_traspaso['Comprador']})",
        )
    else:
        k3.metric("⚡ Mayor Clausulazo", "Sin datos", "Sin traspasos")

    if top_clau is not None:
        k4.metric(
            "🔒 Mayor Subida de Cláusula",
            fmt(top_clau["Precio Operación"]),
            f"{top_clau['Jugador']} ({top_clau['Comprador']})",
        )

    st.divider()

    col_rank1, col_rank2 = st.columns(2)

    with col_rank1:
        st.subheader("🔥 Ranking de Sobrepujadores (% Medio en Mercado)")
        if not df_pujas_mercado.empty:
            df_rank_pujas = (
                df_pujas_mercado.groupby("Comprador")["Sobreprecio (%)"]
                .mean()
                .reset_index()
                .sort_values(by="Sobreprecio (%)", ascending=False)
            )

            fig_rank1 = px.bar(
                df_rank_pujas,
                x="Sobreprecio (%)",
                y="Comprador",
                orientation="h",
                text_auto=".1f",
                color="Sobreprecio (%)",
                color_continuous_scale="Reds",
            )
            fig_rank1.update_layout(
                yaxis={"categoryorder": "total ascending"},
                height=320,
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_rank1, use_container_width=True)

    with col_rank2:
        st.subheader("💰 Ranking de Inversión Total por Mánager")
        df_gastos = (
            df.groupby("Comprador")["Precio Operación"].sum().reset_index()
        )
        df_gastos = df_gastos[df_gastos["Comprador"] != "Mercado"].sort_values(
            by="Precio Operación", ascending=False
        )

        fig_rank2 = px.bar(
            df_gastos,
            x="Precio Operación",
            y="Comprador",
            orientation="h",
            text_auto=".2s",
            color="Precio Operación",
            color_continuous_scale="Blues",
        )
        fig_rank2.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_rank2, use_container_width=True)

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
        m4.metric("Sobrepuja Media", f"+{sobrepuja_media:.1f}%")
    else:
        m4.metric("Sobrepuja Media", "0%")

    st.divider()

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
# PESTAÑA 5: NOTICIAS LIGA BBVA / LALIGA
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
