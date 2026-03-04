import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# =========================================================
# CONFIGURACIÓN
# =========================================================
st.set_page_config(
    layout="wide",
    page_title="Scouting Preferente Femenina",
    page_icon="⚽"
)

# Diccionario de logos normalizado
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
# CARGA DE DATOS
# =========================================================
@st.cache_data
def load_data():
    try:
        # Cargamos el CSV con detección de separador
        df = pd.read_csv("df_finnal.csv", sep=None, engine='python')
        df.columns = df.columns.str.strip()

        # Mapeo de nombres truncados según tu archivo
        rename_dict = {
            'goles_per9': 'goles_per90',
            'goles_reci': 'goles_recibidos_per90',
            'ratio_titula': 'ratio_titularidad',
            'Posición': 'Posicion'
        }
        df = df.rename(columns=rename_dict)

        # Normalización de textos
        if "equipo_key" in df.columns:
            df["equipo_key"] = df["equipo_key"].astype(str).str.strip().str.lower()
        if "Jugadora" in df.columns:
            df["Jugadora"] = df["Jugadora"].astype(str).str.title()
        
        # Limpieza de nulos en Posicion
        if "Posicion" in df.columns:
            df["Posicion"] = df["Posicion"].fillna("N/D")

        # Conversión numérica segura
        cols_num = ["Minutos", "goles_per90", "ratio_titularidad", "goles_recibidos_per90"]
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df
    except Exception as e:
        st.error(f"Error al cargar el CSV: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.stop()

# =========================================================
# INTERFAZ
# =========================================================
st.title("⚽ Dashboard Preferente Femenina Catalunya")

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Análisis Liga",
    "🏟️ Equipos",
    "👤 Perfil Jugadora",
    "🧤 Porteras"
])

# --- TAB 1: LIGA ---
with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Jugadoras", len(df))
    if "goles_per90" in df.columns:
        col2.metric("Promedio Goles/90", f"{df['goles_per90'].mean():.2f}")
        col3.metric("Máximo Goles/90", f"{df['goles_per90'].max():.2f}")

        fig = px.scatter(
            df, x="ratio_titularidad", y="goles_per90",
            size="Minutos", color="equipo_key", hover_name="Jugadora",
            template="plotly_white", title="Relación Titularidad vs Goles"
        )
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: EQUIPOS ---
with tab2:
    if "equipo_key" in df.columns:
        equipos = sorted(df["equipo_key"].unique())
        cols = st.columns(4)
        for i, equipo in enumerate(equipos):
            with cols[i % 4]:
                # Uso del diccionario LOGOS
                logo_file = LOGOS.get(equipo, f"{equipo}.png")
                if os.path.exists(logo_file):
                    st.image(logo_file, width=80)
                
                if st.button(equipo.upper(), key=f"btn_{equipo}", use_container_width=True):
                    st.session_state["equipo_sel"] = equipo

        if "equipo_sel" in st.session_state:
            sel = st.session_state["equipo_sel"]
            df_eq = df[df["equipo_key"] == sel]
            st.markdown(f"### Plantilla {sel.upper()}")
            st.dataframe(df_eq.sort_values("Minutos", ascending=False), use_container_width=True)

# --- TAB 3: PERFIL JUGADORA ---
with tab3:
    # Corrección: Filtro de experiencia como multiselect por ser categórico
    if "experiencia" in df.columns:
        exp_options = sorted(df["experiencia"].unique())
        exp_sel = st.multiselect("Filtrar por Experiencia", exp_options, default=exp_options)
        df_perfil = df[df["experiencia"].isin(exp_sel)]
    else:
        df_perfil = df.copy()

    col_a, col_b = st.columns(2)
    eq_choice = col_a.selectbox("Selecciona Equipo", sorted(df_perfil["equipo_key"].unique()))
    jug_choice = col_b.selectbox("Selecciona Jugadora", df_perfil[df_perfil["equipo_key"] == eq_choice]["Jugadora"])
    
    ficha = df_perfil[df_perfil["Jugadora"] == jug_choice].iloc[0]
    st.header(f"👤 {jug_choice}")
    
    # Radar de Percentiles (Funcional)
    metrics = ["goles_per90", "ratio_titularidad", "Minutos"]
    values = [float((df[m] <= ficha[m]).mean() * 100) for m in metrics if m in df.columns]
    
    fig_radar = go.Figure(go.Scatterpolar(
        r=values + [values[0]], theta=metrics + [metrics[0]], fill='toself'
    ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
    st.plotly_chart(fig_radar, use_container_width=True)

# --- TAB 4: PORTERAS ---
with tab4:
    if "Posicion" in df.columns:
        df_gk = df[df["Posicion"].str.contains("Porter", case=False, na=False)]
        if not df_gk.empty:
            # Corrección: Experiencia como filtro de categorías
            if "experiencia" in df_gk.columns:
                exp_gk = st.multiselect("Nivel de Experiencia", df_gk["experiencia"].unique(), default=df_gk["experiencia"].unique(), key="gk_exp")
                df_gk = df_gk[df_gk["experiencia"].isin(exp_gk)]
            
            st.dataframe(df_gk.sort_values("goles_recibidos_per90"), use_container_width=True)
