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

GOOGLE_DRIVE_URL = "" 

st.markdown(
    """
    <style>
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

    if "compra" in tipo or ("market" in tipo and vendedor == "Mercado"):
        return ["background-color: #e6f0fa; color: #0f3460;"] * len(row)
    elif "venta" in tipo or ("transfer" in tipo and comprador == "Mercado"):
        return ["background-color: #e6ffe6; color: #1b5e20;"] * len(row)
    elif "subasta" in tipo or "auction" in tipo:
        return ["background-color: #ede7f6; color: #512da8; font-weight: bold;"] * len(row)
    elif "clausulazo" in tipo or "clause" in tipo:
        return ["background-color: #ffebee; color: #b71c1c; font-weight: bold;"] * len(row)
    elif "traspaso" in tipo or (vendedor != "Mercado" and comprador != "Mercado"):
        return ["background-color: #fff3e0; color: #e65100;"] * len(row)
    return [""] * len(row)


@st.cache_data(ttl=1800)
def fetch_rss_news():
    fuentes = {
        "Marca": "https://e00-marca.uecdn.es/rss/futbol/primera-division.xml",
        "AS": "https://as.com/rss/futbol/primera.xml",
        "Superdeporte": "https://www.superdeporte.es/rss.html",
    }
    noticias_por_fuente = {nombre: [] for nombre in fuentes.keys()}
    for nombre_fuente, url in fuentes.items():
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            html = urlopen(req).read()
            root = ET.fromstring(html)
            items = root.findall(".//item")
            if not items:
                items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
            for item in items:
                title_el = item.find("title") if item.find("title") is not None else item.find("{http://www.w3.org/2005/Atom}title")
                link_el = item.find("link")
                desc_el = item.find("description") if item.find("description") is not None else item.find("{http://www.w3.org/2005/Atom}summary")
                date_el = item.find("pubDate") if item.find("pubDate") is not None else item.find("{http://www.w3.org/2005/Atom}updated")

                title = title_el.text if title_el is not None and title_el.text else ""
                link = link_el.text if link_el is not None and link_el.text else link_el.attrib.get("href", "")
                desc = desc_el.text if desc_el is not None and desc_el.text else ""
                pubDate = date_el.text if date_el is not None and date_el.text else ""

                if title:
                    noticias_por_fuente[nombre_fuente].append({
                        "Título": title.strip(), "Resumen": desc.strip(), "Fecha": pubDate.strip(), "Enlace": link.strip(), "Fuente": nombre_fuente
                    })
        except Exception:
            continue
    return noticias_por_fuente


def descargar_desde_google_drive_publico():
    csv_file = "historial_biwenger_completo.csv"
    if not GOOGLE_DRIVE_URL:
        return
    try:
        match = re.search(r'/d/([a-zA-Z0-9_-]+)', GOOGLE_DRIVE_URL)
        if match:
            file_id = match.group(1)
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            req = Request(download_url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req) as response, open(csv_file, 'wb') as out_file:
                out_file.write(response.read())
    except Exception:
        pass


def load_data():
    csv_file = "historial_biwenger_completo.csv"
    descargar_desde_google_drive_publico()
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file)
            if "Vendedor" in df.columns:
                df["Vendedor"] = df["Vendedor"].astype(str).str.strip()
            if "Comprador" in df.columns:
                df["Comprador"] = df["Comprador"].astype(str).str.strip()
            return df, csv_file
        except Exception as e:
            st.error(f"Error al leer el archivo CSV: {e}")
            return None, None
    return None, None


df, filename = load_data()

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
    st.warning("No se encuentra el archivo 'historial_biwenger_completo.csv' ni se pudo descargar de Google Drive.")
    st.stop()


def limpiar_tipos(row):
    v = str(row.get("Vendedor", ""))
    c = str(row.get("Comprador", ""))
    t = str(row.get("Tipo", "")).lower()
    if "auction" in t or "subasta" in t:
        return "Subasta"
    elif "market" in t or "compra" in t:
        return "Compra"
    elif ("transfer" in t and c == "Mercado") or "venta" in t:
        return "Venta"
    elif "clause" in t or "clausulazo" in t:
        return "Clausulazo"
    elif v != "Mercado" and c != "Mercado" and v != c:
        return "Traspaso Rival"
    return row.get("Tipo", "Compra")

df["Tipo"] = df.apply(limpiar_tipos, axis=1)

tab_inicio, tab_kpis, tab_mercado, tab_rivales, tab_noticias = st.tabs(
    ["📋 Histórico Completo", "🏆 Récords & KPIs", "📊 Mercado & Pujas", "👥 Rivales & Cláusulas", "📰 Noticias LaLiga"]
)

with tab_inicio:
    st.markdown(
        """
        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; font-size: 0.85rem;">
            <span style="background-color: #e6f0fa; color: #0f3460; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟦 Compra</span>
            <span style="background-color: #e6ffe6; color: #1b5e20; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟩 Venta</span>
            <span style="background-color: #ede7f6; color: #512da8; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟪 Subasta</span>
            <span style="background-color: #fff3e0; color: #e65100; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟧 Traspaso Rival</span>
            <span style="background-color: #ffebee; color: #b71c1c; padding: 4px 8px; border-radius: 4px; font-weight: bold;">🟥 Clausulazo</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    df_inicio = df.copy()
    df_inicio["Sobreprecio (€)"] = df_inicio["Precio Operación"] - df_inicio["Valor Mercado"]
    df_inicio["Sobreprecio (%)"] = (df_inicio["Sobreprecio (€)"] / df_inicio["Valor Mercado"].replace(0, 1)) * 100
    df_inicio["Precio Operación"] = df_inicio["Precio Operación"].apply(fmt)
    df_inicio["Valor Mercado"] = df_inicio["Valor Mercado"].apply(fmt)
    df_inicio["Sobreprecio (€)"] = df_inicio["Sobreprecio (€)"].apply(fmt)
    df_inicio["Sobreprecio (%)"] = df_inicio["Sobreprecio (%)"].apply(fmt_pct)
    
    column_map = {"Fecha": "📅 Fecha", "Jugador": "👤 Jugador", "Vendedor": "🏪 Vendedor", "Comprador": "🛒 Comprador", "Precio Operación": "💰 Precio Operación", "Valor Mercado": "📈 Valor Mercado", "Sobreprecio (€)": "➕ Sobreprecio (€)", "Sobreprecio (%)": "📊 Sobreprecio (%)", "Tipo": "🏷️ Tipo"}
    df_inicio = df_inicio.rename(columns=column_map)
    st.dataframe(df_inicio.style.apply(color_rows, axis=1), hide_index=True, use_container_width=True, height=680)

with tab_kpis:
    st.subheader("🏆 Hall of Fame y Datos Destacados de la Liga")

    PRESUPUESTO_INICIAL = 45_000_000
    todos_los_managers = sorted(list(set(df["Comprador"].dropna()).union(set(df["Vendedor"].dropna()))))
    if "Mercado" in todos_los_managers:
        todos_los_managers.remove("Mercado")

    data_caja = []
    for m in todos_los_managers:
        gasto = df[df["Comprador"] == m]["Precio Operación"].sum()
        ingreso = df[df["Vendedor"] == m]["Precio Operación"].sum()
        caja_estimada = PRESUPUESTO_INICIAL + ingreso - gasto
        data_caja.append({
            "Manager": m,
            "GastoTotal": gasto,
            "IngresoTotal": ingreso,
            "Caja_Estimada": caja_estimada
        })

    df_caja = pd.DataFrame(data_caja).sort_values(by="Caja_Estimada", ascending=False)

    # --- TABLA DE DEBUGAJE TEMPORAL ---
    st.markdown("### 🔍 Panel de Depuración de Caja")
    st.dataframe(df_caja.assign(
        GastoTotal=lambda x: x["GastoTotal"].apply(fmt),
        IngresoTotal=lambda x: x["IngresoTotal"].apply(fmt),
        Caja_Estimada=lambda x: x["Caja_Estimada"].apply(fmt)
    ), use_container_width=True)

    df_caja["Caja_Fmt"] = df_caja["Caja_Estimada"].apply(fmt)

    st.subheader("💵 Dinero en Caja Estimado (Base 45M€)")
    fig_caja = px.bar(
        df_caja, x="Caja_Estimada", y="Manager", orientation="h",
        color="Caja_Estimada", color_continuous_scale="Greens", custom_data=["Caja_Fmt"]
    )
    fig_caja.update_traces(texttemplate="%{customdata[0]}", textposition="outside")
    fig_caja.update_layout(yaxis={"categoryorder": "total ascending", "title": ""}, xaxis={"title": "Euros (€)"}, coloraxis_showscale=False, height=420, margin=dict(l=20, r=50, t=20, b=20))
    st.plotly_chart(fig_caja, use_container_width=True, config=PLOTLY_CONFIG)

with tab_mercado:
    st.subheader("📊 Análisis Global de Mercado")
    df_mercado = df[(df["Vendedor"] == "Mercado") & (df["Tipo"] == "Compra") & (df["Precio Operación"] >= df["Valor Mercado"])].copy()
    st.metric("Total Pujas Mercado", f"{len(df_mercado)}")

with tab_rivales:
    st.subheader("👥 Rivales & Cláusulas")
    todos_managers = [m for m in df["Comprador"].unique() if m != "Mercado"]
    if todos_managers:
        st.selectbox("Selecciona un Manager:", sorted(todos_managers))

with tab_noticias:
    st.subheader("📰 Noticias LaLiga")
    noticias = fetch_rss_news()
    for fuente, lista in noticias.items():
        if lista:
            st.write(f"**{fuente}**: {len(lista)} noticias cargadas.")
