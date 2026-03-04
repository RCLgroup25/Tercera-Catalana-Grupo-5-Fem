import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# =========================================================
# CONFIGURACIÓN
# =========================================================
st.set_page_config(layout="wide", page_title="Gutilytics Scouting", page_icon="⚽")

LOGOS = {
    "fc barcelona c": "barcelona.png",
    "fundacio fb reus": "base reus.png",
    "ce europa b": "europa b.png",
    "fontsanta fatjo": "fontsanta.png",
    "girona fc": "girona.png",
    "cf igualada": "igualada.png",
    "ce mataro": "mataro.png", 
    "vic riuprimer refo": "refo.png",
    "cd riudoms": "riudoms.png",
    "sant cugat fc": "sant cugat.png",
    "ce seagull": "seagull.png",
    "fund ue cornella": "ue cornella.png"
}

# =========================================================
# CARGA Y LIMPIEZA DE DATOS
# =========================================================
@st.cache_data
def load_data():
    file_path = "df_finnal.csv"
    if not os.path.exists(file_path): return pd.DataFrame()
    
    try:
        df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8')
        df.columns = df.columns.str.strip()

        # Mapeo de nombres según tu archivo
        rename_map = {
            'Equipo': 'equipo_key',
            'Posición': 'Posicion',
            'goles_per9': 'goles_per90',
            'ratio_titula': 'ratio_titularidad',
            'goles_reci': 'goles_recibidos_per90',
            'amarillas_': 'amarillas_per90',
            'rojas_per9': 'rojas_per90'
        }
        df = df.rename(columns=rename_map)

        # Limpieza de duplicados (Jugadora única por equipo)
        if "Jugadora" in df.columns and "equipo_key" in df.columns:
            df = df.drop_duplicates(subset=["Jugadora", "equipo_key"])

        # Normalización
        if "equipo_key" in df.columns:
            df["equipo_key"] = df["equipo_key"].astype(str).str.lower().str.strip()
        if "Jugadora" in df.columns:
            df["Jugadora"] = df["Jugadora"].astype(str).str.title().str.strip()
        
        # Conversión numérica
        cols_num = ["Minutos", "goles_per90", "ratio_titularidad", "goles_recibidos_per90", "amarillas_per90", "rojas_per90", "Goles"]
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        return df
    except:
        return pd.DataFrame()

df_raw = load_data()

if df_raw.empty:
    st.error("Error al cargar datos.")
    st.stop()

# =========================================================
# SIDEBAR - FILTROS GLOBALES
# =========================================================
st.sidebar.header("🔍 Filtros Globales")
max_min = int(df_raw["Minutos"].max())
min_minutos = st.sidebar.slider("Minutos mínimos jugados", 0, max_min, 100)
df = df_raw[df_raw["Minutos"] >= min_minutos].copy()

# =========================================================
# CUERPO PRINCIPAL
# =========================================================
st.title("⚽ Dashboard Preferente Femenina Catalunya")

tabs = st.tabs(["📈 Análisis Liga", "🏟️ Equipos", "🧤 Porteras"])

# --- TAB 1: ANÁLISIS LIGA ---
with tabs[0]:
    # Métricas principales
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jugadoras en muestra", len(df))
    c2.metric("Prom. Goles/90", f"{df['goles_per90'].mean():.2f}")
    c3.metric("Prom. Amarillas/90", f"{df['amarillas_per90'].mean():.2f}")
    c4.metric("Máx. Goles/90", f"{df['goles_per90'].max():.2f}")

    # Gráfico de dispersión
    fig = px.scatter(df, x="ratio_titularidad", y="goles_per90", size="Minutos", 
                     color="equipo_key", hover_name="Jugadora", 
                     title="Eficiencia Goleadora vs Titularidad",
                     template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    # Top 10 Goleadoras Eficientes
    st.markdown("### 🔝 Top 10 Goleadoras Eficientes")
    top_10 = df.nlargest(10, "goles_per90")[["Jugadora", "equipo_key", "Goles", "goles_per90", "Minutos"]]
    st.table(top_10.style.format({"goles_per90": "{:.2f}"}))

# --- TAB 2: EQUIPOS ---
with tabs[1]:
    equipos = sorted(df["equipo_key"].unique())
    cols_grid = st.columns(6) # Más columnas para que los logos no ocupen tanto espacio
    
    for i, eq in enumerate(equipos):
        with cols_grid[i % 6]:
            logo_fn = LOGOS.get(eq, "")
            if os.path.exists(logo_fn):
                st.image(logo_fn, width=50)
            if st.button(eq.upper(), key=f"btn_{eq}", use_container_width=True):
                st.session_state["sel_eq"] = eq

    if "sel_eq" in st.session_state:
        target = st.session_state["sel_eq"]
        st.subheader(f"📊 Análisis: {target.upper()}")
        
        # Tabla resumida con métricas clave
        df_eq = df[df["equipo_key"] == target].sort_values("Minutos", ascending=False)
        cols_view = ["Jugadora", "Minutos", "Goles", "goles_per90", "amarillas_per90", "rojas_per90", "ratio_titularidad"]
        
        st.dataframe(df_eq[cols_view].style.format({
            "goles_per90": "{:.2f}",
            "amarillas_per90": "{:.2f}",
            "rojas_per90": "{:.2f}",
            "ratio_titularidad": "{:.2f}"
        }), use_container_width=True, hide_index=True)

# --- TAB 3: PORTERAS ---
with tabs[2]:
    st.subheader("🧤 Rendimiento bajo palos")
    if "Posicion" in df.columns:
        df_gk = df[df["Posicion"].str.contains("Porter|GK", case=False, na=False)].copy()
        
        if not df_gk.empty:
            # Tabla acortada de porteras
            cols_gk = ["Jugadora", "equipo_key", "Minutos", "Goles", "goles_recibidos_per90", "ratio_titularidad"]
            st.dataframe(df_gk[cols_gk].sort_values("goles_recibidos_per90").style.format({
                "goles_recibidos_per90": "{:.2f}",
                "ratio_titularidad": "{:.2f}"
            }), use_container_width=True, hide_index=True)
        else:
            st.info("No se encontraron jugadoras en posición de Portera con el filtro de minutos actual.")
