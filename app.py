import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# =========================================================
# CONFIGURACIÓN DE PÁGINA
# =========================================================
st.set_page_config(
    layout="wide",
    page_title="Scouting Preferente Femenina",
    page_icon="⚽"
)

# =========================================================
# ESTILO
# =========================================================
st.markdown("""
<style>
.stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; }
div.stButton > button { border-radius: 10px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# CARGA DE DATOS (CSV)
# =========================================================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("df_finnal.csv")
        df.columns = df.columns.str.strip()

        if "equipo_key" in df.columns:
            df["equipo_key"] = df["equipo_key"].astype(str).str.strip().str.lower()

        if "Jugadora" in df.columns:
            df["Jugadora"] = df["Jugadora"].astype(str).str.title()

        if "Posición" in df.columns:
            df["Posición"] = df["Posición"].fillna("N/D")

        if "Minutos" in df.columns:
            df["Minutos"] = pd.to_numeric(df["Minutos"], errors="coerce").fillna(0)

        return df

    except Exception as e:
        st.error(f"Error cargando CSV: {e}")
        return pd.DataFrame()

df = load_data()

# =========================================================
# DEBUG SIDEBAR
# =========================================================
st.sidebar.header("Estado de datos")
st.sidebar.write("Jugadoras cargadas:", len(df))

if df.empty:
    st.error("El CSV no se está leyendo. Verifica que df_finnal.csv esté junto a app.py.")
    st.stop()

# =========================================================
# TÍTULO
# =========================================================
st.title("⚽ Dashboard Preferente Femenina Catalunya")

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Análisis Liga",
    "🏟️ Equipos",
    "👤 Perfil Jugadora",
    "🧤 Porteras"
])

# =========================================================
# TAB 1 - ANÁLISIS LIGA
# =========================================================
with tab1:

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Jugadoras", len(df))

    if "goles_per90" in df.columns:
        col2.metric("Promedio Goles/90", f"{df['goles_per90'].mean():.2f}")
        col3.metric("Máximo Goles/90", f"{df['goles_per90'].max():.2f}")

        fig = px.scatter(
            df,
            x="ratio_titularidad" if "ratio_titularidad" in df.columns else df.columns[0],
            y="goles_per90",
            size="Minutos" if "Minutos" in df.columns else None,
            color="equipo_key" if "equipo_key" in df.columns else None,
            hover_name="Jugadora" if "Jugadora" in df.columns else None,
            template="plotly_white"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No existe la columna goles_per90 en el CSV.")

# =========================================================
# TAB 2 - EQUIPOS
# =========================================================
with tab2:

    if "equipo_key" not in df.columns:
        st.warning("No existe la columna equipo_key.")
    else:
        equipos = sorted(df["equipo_key"].unique())
        cols = st.columns(4)

        for i, equipo in enumerate(equipos):
            with cols[i % 4]:
                if st.button(equipo.upper(), use_container_width=True):
                    st.session_state["equipo_sel"] = equipo

        if "equipo_sel" in st.session_state:
            eq = st.session_state["equipo_sel"]
            df_eq = df[df["equipo_key"] == eq]

            st.markdown(f"### Plantilla {eq.upper()}")
            st.dataframe(df_eq, use_container_width=True)

# =========================================================
# TAB 3 - PERFIL JUGADORA
# =========================================================
with tab3:

    if "equipo_key" in df.columns and "Jugadora" in df.columns:

        eq_choice = st.selectbox("Equipo", sorted(df["equipo_key"].unique()))
        df_eq = df[df["equipo_key"] == eq_choice]

        jug_choice = st.selectbox("Jugadora", df_eq["Jugadora"])

        ficha = df_eq[df_eq["Jugadora"] == jug_choice].iloc[0]

        st.markdown(f"## {jug_choice}")

        col1, col2, col3 = st.columns(3)

        if "Minutos" in df.columns:
            col1.metric("Minutos", int(ficha["Minutos"]))

        if "goles_per90" in df.columns:
            col2.metric("Goles/90", f"{ficha['goles_per90']:.2f}")

        if "ratio_titularidad" in df.columns:
            col3.metric("Ratio Titular", f"{ficha['ratio_titularidad']:.2f}")

        # Radar simple si existen métricas
        metrics = [m for m in ["goles_per90", "ratio_titularidad", "Minutos"] if m in df.columns]

        if len(metrics) >= 2:
            values = [(df[m] <= ficha[m]).mean() * 100 for m in metrics]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=metrics + [metrics[0]],
                fill="toself"
            ))

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 4 - PORTERAS
# =========================================================
with tab4:

    if "Posición" in df.columns:
        df_gk = df[df["Posición"].str.contains("Porter", case=False, na=False)]

        if not df_gk.empty and "goles_recibidos_per90" in df.columns:
            st.metric("Porteras", len(df_gk))
            st.dataframe(
                df_gk.sort_values("goles_recibidos_per90"),
                use_container_width=True
            )
        else:
            st.info("No hay porteras detectadas o falta la métrica goles_recibidos_per90.")
    else:
        st.info("No existe la columna Posición.")