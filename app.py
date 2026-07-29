import os
import base64
import re
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen

import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from PIL import Image
except ImportError:
    Image = None

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
    /* Ocultar barra lateral por completo */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    .leyenda-item, div[data-testid="stHorizontalBlock"] button {
        color: #000000 !important;
        font-weight: 600 !important;
        opacity: 1 !important;
        filter: none !important;
        border: none !important;
        box-shadow: none !important;
    }
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
    }
    .header-title-wrapper {
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .header-title-text {
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.25;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

PLOTLY_CONFIG = {"displayModeBar": False}


# ==========================================
# FUNCIONES AUXILIARES
# ==========================================
def fmt(val):
    if pd.isna(val) or val is None:
        return "-"
    return f"{val:,.1f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(val):
    if pd.isna(val) or val is None:
        return "-"
    signo = "+" if val > 0 else ""
    return f"{signo}{val:,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def color_rows(row):
    tipo = str(row.get("🏷️ Tipo", row.get("Tipo", ""))).lower()
    vendedor = str(row.get("🏪 Vendedor", row.get("Vendedor", "")))
    comprador = str(row.get("🛒 Comprador", row.get("Comprador", "")))

    if "market" in tipo and vendedor == "Mercado":
        return ["background-color: #e6f0fa; color: #0f3460;"] * len(row)
    elif "transfer" in tipo and comprador == "Mercado":
        return ["background-color: #e6ffe6; color: #1b5e20;"] * len(row)
    elif "clause" in tipo or "subida" in tipo or "clausulazo" in tipo:
        return ["background-color: #ffebee; color: #b71c1c; font-weight: bold;"] * len(row)
    elif vendedor != "Mercado" and comprador != "Mercado":
        # Identificación inteligente entre Acuerdo (Naranja) y Clausulazo (Rojo)
        # Si el precio es significativamente mayor al valor de mercado o se detecta como traspaso entre rivales
        if "clausulazo" in tipo or "clause" in tipo or "release" in tipo:
            return ["background-color: #ffebee; color: #b71c1c; font-weight: bold;"] * len(row)
        else:
            # Si el tipo es 'transfer' entre usuarios pero queremos forzar si es clausulazo real por sobreprecio o ID
            return ["background-color: #fff3e0; color: #e65100;"] * len(row)
    return [""] * len(row)


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
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                desc = item.find("description").text if item.find("description") is not None else ""
                pubDate = item.find("pubDate").text if item.find("pubDate") is not None else ""

                desc_clean = desc.replace("<p>", "").replace("</p>", "").replace("<br>", "\n")
                if "<" in desc_clean and ">" in desc_clean:
                    desc_clean = re.sub("<[^<]+?>", "", desc_clean)

                if title:
                    noticias.append({
                        "Título": title,
                        "Resumen": desc_clean.strip(),
                        "Fecha": pubDate,
                        "Enlace": link,
                    })
        except Exception:
            continue
    return noticias


@st.cache_data(ttl=300)
def load_data():
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

# --- HEADER SUPERIOR ---
col_head_1, col_head_2 = st.columns([8, 2], vertical_alignment="center")

posibles_rutas = ["logo1.png", "assets/logo1.png", "img/logo1.png", "images/logo1.png"]
logo_encontrado = None
for ruta in posibles_rutas:
    if os.path.exists(ruta):
        logo_encontrado = ruta
        break

with col_head_1:
    if logo_encontrado:
        with open(logo_encontrado, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f"""
            <div class="header-title-wrapper">
                <img src="data:image/png;base64,{encoded_string}" style="width: 85px; height: auto; border-radius: 8px;">
                <div class="header-title-text">¡Bienvenidos a la mejor liga del mundo! Y al mejor análisis del mundo, ¡Conde News!</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="header-title-wrapper">
                <div style="font-size: 3.5rem;">🧛‍♂️</div>
                <div class="header-title-text">¡Bienvenidos a la mejor liga del mundo! Y al mejor análisis del mundo, ¡Conde News!</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with col_head_2:
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

if df is None or df.empty:
    st.info("Cargando datos o esperando primera actualización...")
    st.stop()

# --- RECLASIFICACIÓN AUTOMÁTICA EN CASO DE NECESIDAD (Clausulazos reales entre rivales) ---
# Si un mánager le compra a otro mánager y el sobreprecio es masivo o viene de cláusula, lo etiquetamos visualmente
def corregir_tipo_excepcional(row):
    v = str(row.get("Vendedor", ""))
    c = str(row.get("Comprador", ""))
    t = str(row.get("Tipo", "")).lower()
    if v != "Mercado" and c != "Mercado" and v != c:
        if "transfer" in t:
            # En Biwenger, los clausulazos entre usuarios suelen tener un sobreprecio gigante o se registran como transfer
            return "Clausulazo Rival"
    return row.get("Tipo", "")

df["Tipo"] = df.apply(corregir_tipo_excepcional, axis=1)

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
# PESTAÑA 1: HISTÓRICO COMPLETO CON FILTROS
# ==========================================
with tab_inicio:
    st.markdown(
        """
        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; font-size: 0.85rem;">
            <span style="background-color: #e6f0fa; color: #0f3460; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟦 Compra Mercado</span>
            <span style="background-color: #e6ffe6; color: #1b5e20; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟩 Venta Mercado</span>
            <span style="background-color: #f3e8ff; color: #4a154b; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟪 Subida Cláusula</span>
            <span style="background-color: #fff3e0; color: #e65100; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟧 Acuerdo / Traspaso Rival</span>
            <span style="background-color: #ffebee; color: #b71c1c; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟥 Clausulazo Rival</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- ZONA DE FILTROS INTERACTIVOS POR COLUMNA (TICK MARKS) ---
    with st.expander("🔍 Filtrar columnas (Selecciona los campos que deseas ver)", expanded=False):
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            all_vendedores = sorted(df["Vendedor"].dropna().unique().tolist())
            sel_vendedores = st.multiselect("Filtrar por Vendedor:", options=all_vendedores, default=all_vendedores)
            
        with f_col2:
            all_compradores = sorted(df["Comprador"].dropna().unique().tolist())
            sel_compradores = st.multiselect("Filtrar por Comprador:", options=all_compradores, default=all_compradores)
            
        with f_col3:
            all_tipos = sorted(df["Tipo"].dropna().unique().tolist())
            sel_tipos = st.multiselect("Filtrar por Tipo:", options=all_tipos, default=all_tipos)

    # Aplicar filtros seleccionados
    df_filtrado = df[
        df["Vendedor"].isin(sel_vendedores) &
        df["Comprador"].isin(sel_compradores) &
        df["Tipo"].isin(sel_tipos)
    ].copy()

    st.caption(f"Mostrando {len(df_filtrado)} registros (filtrados de un total de {len(df)}).")

    df_inicio = df_filtrado.copy()
    df_inicio["_Precio_Num"] = df_inicio["Precio Operación"]
    df_inicio["_VM_Num"] = df_inicio["Valor Mercado"]
    df_inicio["Sobreprecio (€)"] = df_inicio["Precio Operación"] - df_inicio["Valor Mercado"]
    df_inicio["Sobreprecio (%)"] = (df_inicio["Sobreprecio (€)"] / df_inicio["Valor Mercado"].replace(0, 1)) * 100

    df_inicio_formatted = df_inicio.copy()
    df_inicio_formatted["Precio Operación"] = df_inicio_formatted["Precio Operación"].apply(fmt)
    df_inicio_formatted["Valor Mercado"] = df_inicio_formatted["Valor Mercado"].apply(fmt)
    df_inicio_formatted["Sobreprecio (€)"] = df_inicio_formatted["Sobreprecio (€)"].apply(fmt)
    df_inicio_formatted["Sobreprecio (%)"] = df_inicio_formatted["Sobreprecio (%)"].apply(fmt_pct)

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
    df_styled = df_inicio_formatted[cols_mostrar + ["_Precio_Num", "_VM_Num"]].style.apply(color_rows, axis=1)

    st.dataframe(
        df_styled,
        column_order=cols_mostrar,
        hide_index=True,
        use_container_width=True,
        height=680,
    )

# ==========================================
# PESTAÑA 2: RÉCORDS & KPIS
# ==========================================
with tab_kpis:
    st.subheader("🏆 Hall of Fame y Datos Destacados de la Liga")

    df_pujas_mercado = df[
        (df["Vendedor"] == "Mercado")
        & (df["Tipo"] == "market")
        & (df["Precio Operación"] >= df["Valor Mercado"])
    ].copy()

    df_pujas_mercado["Sobreprecio (€)"] = df_pujas_mercado["Precio Operación"] - df_pujas_mercado["Valor Mercado"]
    df_pujas_mercado["Sobreprecio (%)"] = (df_pujas_mercado["Sobreprecio (€)"] / df_pujas_mercado["Valor Mercado"]) * 100

    top_puja = df_pujas_mercado.loc[df_pujas_mercado["Precio Operación"].idxmax()] if not df_pujas_mercado.empty else None
    top_locura_pct = df_pujas_mercado.loc[df_pujas_mercado["Sobreprecio (%)"].idxmax()] if not df_pujas_mercado.empty else None

    df_entre_rivales = df[(df["Vendedor"] != "Mercado") & (df["Comprador"] != "Mercado") & (df["Vendedor"] != df["Comprador"])]
    top_traspaso = df_entre_rivales.loc[df_entre_rivales["Precio Operación"].idxmax()] if not df_entre_rivales.empty else None

    df_clau_all = df[df["Tipo"].str.contains("clause|subida|clausulazo", case=False, na=False)]
    top_clau = df_clau_all.loc[df_clau_all["Precio Operación"].idxmax()] if not df_clau_all.empty else None

    k1, k2 = st.columns(2)
    if top_puja is not None:
        k1.metric("🎯 Mayor Puja Mercado", fmt(top_puja["Precio Operación"]), f"{top_puja['Jugador']}")
    if top_locura_pct is not None:
        k2.metric("🚀 Mayor Sobrepuja (%)", fmt_pct(top_locura_pct["Sobreprecio (%)"]), f"{top_locura_pct['Jugador']}")

    st.markdown("<br>", unsafe_allow_html=True)

    k3, k4 = st.columns(2)
    if top_traspaso is not None:
        k3.metric("⚡ Mayor Traspaso", fmt(top_traspaso["Precio Operación"]), f"{top_traspaso['Jugador']}")
    else:
        k3.metric("⚡ Mayor Traspaso", "Sin datos", "Sin registros")

    if top_clau is not None:
        k4.metric("🔒 Mayor Subida Cláusula", fmt(top_clau["Precio Operación"]), f"{top_clau['Jugador']}")

    st.divider()

    PRESUPUESTO_INICIAL = 45_000_000
    df_gastos_tot = df[df["Comprador"] != "Mercado"].groupby("Comprador")["Precio Operación"].sum().reset_index()
    df_gastos_tot.columns = ["Manager", "GastoTotal"]
    df_ventas_tot = df[df["Vendedor"] != "Mercado"].groupby("Vendedor")["Precio Operación"].sum().reset_index()
    df_ventas_tot.columns = ["Manager", "IngresoTotal"]

    df_caja = pd.merge(df_gastos_tot, df_ventas_tot, on="Manager", how="outer").fillna(0)
    df_caja["Caja_Estimada"] = PRESUPUESTO_INICIAL + df_caja["IngresoTotal"] - df_caja["GastoTotal"]
    df_caja = df_caja.sort_values(by="Caja_Estimada", ascending=False)
    df_caja["Caja_Fmt"] = df_caja["Caja_Estimada"].apply(fmt)

    st.subheader("💵 Dinero en Caja Estimado (Base 45M€)")
    fig_caja = px.bar(
        df_caja, x="Caja_Estimada", y="Manager", orientation="h",
        color="Caja_Estimada", color_continuous_scale="Greens", custom_data=["Caja_Fmt"]
    )
    fig_caja.update_traces(texttemplate="%{customdata[0]}", textposition="outside")
    fig_caja.update_layout(yaxis={"categoryorder": "total ascending", "title": ""}, xaxis={"title": "Euros (€)"}, coloraxis_showscale=False, height=450, margin=dict(l=20, r=50, t=20, b=20))
    st.plotly_chart(fig_caja, use_container_width=True, config=PLOTLY_CONFIG)

# ==========================================
# PESTAÑA 3: MERCADO & SOBREPUJAS
# ==========================================
with tab_mercado:
    st.subheader("📊 Análisis Global de Mercado")
    df_mercado = df[(df["Vendedor"] == "Mercado") & (df["Tipo"].str.contains("market", case=False, na=False)) & (df["Precio Operación"] >= df["Valor Mercado"])].copy()
    df_mercado["Sobreprecio (€)"] = df_mercado["Precio Operación"] - df_mercado["Valor Mercado"]
    df_mercado["Sobreprecio (%)"] = (df_mercado["Sobreprecio (€)"] / df_mercado["Valor Mercado"]) * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pujas Mercado", f"{len(df_mercado)}")
    c2.metric("Sobrepuja Media Liga", fmt_pct(df_mercado["Sobreprecio (%)"].mean()))
    c3.metric("Sobrepuja Mediana Liga", fmt_pct(df_mercado["Sobreprecio (%)"].median()))

    st.divider()
    st.subheader("🔥 Top 10 Fichajes Más Caros del Mercado")
    top10 = df_mercado.nlargest(10, "Precio Operación").copy()
    top10["Precio_Fmt"] = top10["Precio Operación"].apply(fmt)
    fig = px.bar(top10, x="Precio Operación", y="Jugador", color="Comprador", orientation="h", custom_data=["Precio_Fmt", "Comprador"])
    fig.update_traces(texttemplate="%{customdata[0]}", textposition="outside")
    fig.update_layout(yaxis={"categoryorder": "total ascending", "title": ""}, height=380, margin=dict(l=20, r=50, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

# ==========================================
# PESTAÑA 4: RIVALES & CLÁUSULAS
# ==========================================
with tab_rivales:
    todos_managers = set(df["Comprador"].unique()).union(set(df["Vendedor"].unique()))
    if "Mercado" in todos_managers:
        todos_managers.remove("Mercado")

    rival_seleccionado = st.selectbox("🔍 Selecciona un Manager:", sorted(list(todos_managers)))

    df_compras_mercado = df[(df["Comprador"] == rival_seleccionado) & (df["Vendedor"] == "Mercado") & (df["Tipo"].str.contains("market", case=False, na=False)) & (df["Precio Operación"] >= df["Valor Mercado"])].copy()
    df_ventas = df[df["Vendedor"] == rival_seleccionado].copy()
    df_clausulas = df[(df["Comprador"] == rival_seleccionado) & (df["Tipo"].str.contains("clause|subida|clausulazo", case=False, na=False))].copy()
    df_robados = df[(df["Comprador"] == rival_seleccionado) & (df["Vendedor"] != "Mercado") & (df["Vendedor"] != rival_seleccionado)].copy()
    df_perdidos = df[(df["Vendedor"] == rival_seleccionado) & (df["Comprador"] != "Mercado") & (df["Comprador"] != rival_seleccionado)].copy()

    gasto_total_general = df_compras_mercado["Precio Operación"].sum() + df_clausulas["Precio Operación"].sum() + df_robados["Precio Operación"].sum()
    ingreso_ventas = df_ventas["Precio Operación"].sum()
    balance_neto = ingreso_ventas - gasto_total_general

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Gasto Total", fmt(gasto_total_general))
    m2.metric("Ingresos Ventas", fmt(ingreso_ventas))
    m3.metric("Balance Neto", fmt(balance_neto), delta="Superávit" if balance_neto >= 0 else "Déficit")
    
    sobrepuja_media = ((df_compras_mercado["Precio Operación"] - df_compras_mercado["Valor Mercado"]) / df_compras_mercado["Valor Mercado"] * 100).mean() if not df_compras_mercado.empty else 0.0
    m4.metric("Sobrepuja Media", fmt_pct(sobrepuja_media))

    st.divider()
    st.subheader(f"🛒 Pujas de Mercado ({len(df_compras_mercado)} fichajes)")
    if df_compras_mercado.empty:
        st.info("Sin fichajes directos de mercado.")
    else:
        top_compras_rival = df_compras_mercado.nlargest(8, "Precio Operación").copy()
        top_compras_rival["Precio_Fmt"] = top_compras_rival["Precio Operación"].apply(fmt)
        fig_compras = px.bar(top_compras_rival, x="Jugador", y="Precio Operación", color="Valor Mercado")
        st.plotly_chart(fig_compras, use_container_width=True, config=PLOTLY_CONFIG)

# ==========================================
# PESTAÑA 5: NOTICIAS LALIGA
# ==========================================
with tab_noticias:
    st.subheader("📰 Noticias LaLiga & Rumores de Fichajes")
    noticias = fetch_rss_news()
    if not noticias:
        st.warning("No se han podido cargar las noticias en este momento.")
    else:
        busqueda = st.text_input("🔍 Buscar jugador o equipo en noticias:", placeholder="Ej: Mbappe, Williams, Betis...")
        noticias_filtradas = [n for n in noticias if busqueda.lower() in n["Título"].lower() or busqueda.lower() in n["Resumen"].lower()]
        for noticia in noticias_filtradas[:25]:
            with st.expander(f"📌 {noticia['Título']}"):
                if noticia["Fecha"]:
                    st.caption(f"🗓️ {noticia['Fecha']}")
                st.write(noticia["Resumen"])
                if noticia["Enlace"]:
                    st.markdown(f"[🔗 Leer noticia completa en la web]({noticia['Enlace']})")
