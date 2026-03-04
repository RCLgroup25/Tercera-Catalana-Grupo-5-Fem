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

# Diccionario de logos proporcionado
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
# CARGA DE DATOS (PROTEGIDA)
# =========================================================
@st.cache_data
def load_data():
    file_path = "df_finnal.csv"
    if not os.path.exists(file_path):
        return pd.DataFrame()
    
    try:
        # Cargamos el CSV detectando separador automáticamente
        df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8')
        df.columns = df.columns.str.strip()

        # Mapeo de columnas según capturas anteriores
        rename_map = {
            'Equipo': 'equipo_key',
            'Posición': 'Posicion',
            'goles_per9': 'goles_per90',
            'ratio_titula': 'ratio_titularidad',
            'goles_reci': 'goles_recibidos_per90'
        }
        df = df.rename(columns=rename_map)

        # Normalización de textos para que coincidan con el diccionario LOGOS
        if "equipo_key" in df.columns:
            df["equipo_key"] = df["equipo_key"].astype(str).str.strip().str.lower()
        if "Jugadora" in df.columns:
            df["Jugadora"] = df["Jugadora"].astype(str).str.strip().str.title()
        
        # Conversión numérica forzada para evitar el error de "redacted message"
        cols_a_convertir = ["Minutos", "goles_per90", "ratio_titularidad", "goles_recibidos_per90"]
        for col in cols_a_convertir:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error en la lectura: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No se pudieron cargar los datos. Verifica el archivo CSV.")
    st.stop()

# =========================================================
# INTERFAZ PRINCIPAL
# =========================================================
st.title("⚽ Dashboard Preferente Femenina Catalunya")

tabs = st.tabs(["📈 Análisis Liga", "🏟️ Equipos", "👤 Perfil Jugadora", "🧤 Porteras"])

# --- TAB 1: ANÁLISIS LIGA ---
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    c1.metric("Jugadoras", len(df))
    if "goles_per90" in df.columns:
        c2.metric("G/90 Promedio", f"{df['goles_per90'].mean():.2f}")
        c3.metric("Máximo G/90", f"{df['goles_per90'].max():.2f}")
    
    fig = px.scatter(df, x="ratio_titularidad", y="goles_per90", size="Minutos", 
                     color="equipo_key", hover_name="Jugadora", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: EQUIPOS (LOGOS INTEGRADOS) ---
with tabs[1]:
    equipos = sorted(df["equipo_key"].unique())
    cols_grid = st.columns(4)
    
    for i, eq in enumerate(equipos):
        with cols_grid[i % 4]:
            # Buscamos el logo en el diccionario o usamos el nombre como fallback
            logo_fn = LOGOS.get(eq, f"{eq}.png")
            if os.path.exists(logo_fn):
                st.image(logo_fn, width=70)
            
            if st.button(eq.upper(), key=f"btn_{eq}", use_container_width=True):
                st.session_state["sel_equipo"] = eq

    if "sel_equipo" in st.session_state:
        eq_name = st.session_state["sel_equipo"]
        st.subheader(f"Plantilla: {eq_name.upper()}")
        st.dataframe(df[df["equipo_key"] == eq_name].sort_values("Minutos", ascending=False), use_container_width=True)

# --- TAB 3: PERFIL JUGADORA (FIX EXPERIENCIA) ---
with tabs[2]:
    # SOLUCIÓN AL ERROR: Multiselect para valores categóricos
    if "experiencia" in df.columns:
        opciones_exp = sorted(df["experiencia"].unique().tolist())
        filtro_exp = st.multiselect("Filtrar por Nivel de Experiencia", opciones_exp, default=opciones_exp)
        df_p = df[df["experiencia"].isin(filtro_exp)]
    else:
        df_p = df.copy()

    col_l, col_r = st.columns(2)
    e_sel = col_l.selectbox("Equipo", sorted(df_p["equipo_key"].unique()))
    j_sel = col_r.selectbox("Jugadora", df_p[df_p["equipo_key"] == e_sel]["Jugadora"])
    
    ficha = df_p[df_p["Jugadora"] == j_sel].iloc[0]
    st.header(f"👤 {j_sel}")
    
    # Radar simple
    metrics = ["goles_per90", "ratio_titularidad", "Minutos"]
    vals = [float((df[m] <= ficha[m]).mean() * 100) for m in metrics if m in df.columns]
    
    fig_radar = go.Figure(go.Scatterpolar(r=vals + [vals[0]], theta=metrics + [metrics[0]], fill='toself'))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
    st.plotly_chart(fig_radar, use_container_width=True)

# --- TAB 4: PORTERAS ---
with tabs[3]:
    if "Posicion" in df.columns:
        # Filtrado flexible
        df_gk = df[df["Posicion"].str.contains("Porter|GK", case=False, na=False)]
        if not df_gk.empty:
            if "experiencia" in df_gk.columns:
                # Evitamos el error de int() usando multiselect nuevamente
                exp_gk = st.multiselect("Experiencia Porteras", df_gk["experiencia"].unique(), default=df_gk["experiencia"].unique())
                df_gk = df_gk[df_gk["experiencia"].isin(exp_gk)]
            
            st.dataframe(df_gk.sort_values("goles_recibidos_per90"), use_container_width=True)
