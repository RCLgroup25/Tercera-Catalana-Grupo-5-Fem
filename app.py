import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# =========================================================
# CONFIGURACIÓN
# =========================================================
st.set_page_config(layout="wide", page_title="Gutilytics Intelligence Scouting", page_icon="⚽")

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

@st.cache_data
def load_data():
    file_path = "df_finnal.csv"
    if not os.path.exists(file_path): return pd.DataFrame()
    try:
        df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8')
        df.columns = df.columns.str.strip()
        
        rename_map = {
            'Equipo': 'equipo_key', 'Posición': 'Posicion',
            'goles_per9': 'goles_per90', 'ratio_titula': 'ratio_titularidad',
            'goles_reci': 'goles_recibidos_per90', 'amarillas_': 'amarillas_per90',
            'rojas_per9': 'rojas_per90'
        }
        df = df.rename(columns=rename_map)
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
    except: return pd.DataFrame()

df_raw = load_data()

# --- SIDEBAR ---
st.sidebar.header("🔍 Filtros Globales")
min_minutos = st.sidebar.slider("Minutos mínimos", 0, int(df_raw["Minutos"].max()), 100)
df = df_raw[df_raw["Minutos"] >= min_minutos].copy()

# --- CUERPO ---
st.title("⚽ Dashboard Tercera Federación Grupo 5")

tabs = st.tabs(["📈 Análisis Liga", "🏟️ Equipos", "🧤 Porteras"])

# --- TAB 1: ANÁLISIS LIGA ---
with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jugadoras", len(df))
    c2.metric("Prom. Goles/90", f"{df['goles_per90'].mean():.2f}")
    c3.metric("Prom. Amarillas/90", f"{df['amarillas_per90'].mean():.2f}")
    c4.metric("Goles Totales Liga", int(df['Goles'].sum()))

    # --- NUEVO: Gráfico de Goles Totales por Equipo ---
    st.markdown("### 📊 Volumen de Goles por Equipo")
    goles_equipo = df.groupby("equipo_key")["Goles"].sum().reset_index().sort_values("Goles", ascending=False)
    fig_goles = px.bar(goles_equipo, x="equipo_key", y="Goles", color="Goles",
                       color_continuous_scale="Viridis", template="plotly_white",
                       labels={"equipo_key": "Equipo", "Goles": "Goles Totales"})
    st.plotly_chart(fig_goles, use_container_width=True)

    col_left, col_right = st.columns(2)
    
    with col_left:
        # --- NUEVO: Visualización del Proxy de Experiencia ---
        st.markdown("### 🧬 Composición por Experiencia (Proxy)")
        if "experiencia" in df.columns:
            # Conteo de categorías de experiencia
            exp_dist = df["experiencia"].value_counts().reset_index()
            exp_dist.columns = ["Experiencia", "Cantidad"]
            fig_exp = px.pie(exp_dist, names="Experiencia", values="Cantidad", 
                             hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_exp, use_container_width=True)
        else:
            st.info("Columna 'experiencia' no encontrada.")

    with col_right:
        st.markdown("### 🔝 Top 10 Goleadoras Eficientes")
        top_10 = df.nlargest(10, "goles_per90")[["Jugadora", "equipo_key", "Goles", "goles_per90"]]
        st.dataframe(top_10.style.format({"goles_per90": "{:.2f}"}), hide_index=True)

# --- TAB 2: EQUIPOS ---
with tabs[1]:
    equipos = sorted(df["equipo_key"].unique())
    cols_grid = st.columns(6)
    for i, eq in enumerate(equipos):
        with cols_grid[i % 6]:
            logo_fn = LOGOS.get(eq, "")
            if os.path.exists(logo_fn): st.image(logo_fn, width=50)
            if st.button(eq.upper(), key=f"btn_{eq}", use_container_width=True):
                st.session_state["sel_eq"] = eq

    if "sel_eq" in st.session_state:
        target = st.session_state["sel_eq"]
        st.subheader(f"📊 Plantilla: {target.upper()}")
        df_eq = df[df["equipo_key"] == target].sort_values("Minutos", ascending=False)
        # Mostrar métrica de experiencia promedio del equipo si es posible
        cols_view = ["Jugadora", "experiencia", "Minutos", "Goles", "goles_per90", "amarillas_per90", "ratio_titularidad"]
        st.dataframe(df_eq[cols_view].style.format({
            "goles_per90": "{:.2f}", "amarillas_per90": "{:.2f}", "ratio_titularidad": "{:.2f}"
        }), use_container_width=True, hide_index=True)

# --- TAB 3: PORTERAS ---
with tabs[2]:
    st.subheader("🧤 Rendimiento Porteras")
    if "Posicion" in df.columns:
        df_gk = df[df["Posicion"].str.contains("Porter|GK", case=False, na=False)].copy()
        if not df_gk.empty:
            cols_gk = ["Jugadora", "equipo_key", "experiencia", "Minutos", "Goles", "goles_recibidos_per90", "ratio_titularidad"]
            st.dataframe(df_gk[cols_gk].sort_values("goles_recibidos_per90").style.format({
                "goles_recibidos_per90": "{:.2f}", "ratio_titularidad": "{:.2f}"
            }), use_container_width=True, hide_index=True)


