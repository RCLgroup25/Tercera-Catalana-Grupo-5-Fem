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
# CARGA DE DATOS
# =========================================================
@st.cache_data
def load_data():
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

    # Eliminar duplicados
    if "Jugadora" in df.columns and "equipo_key" in df.columns:
        df = df.drop_duplicates(subset=["Jugadora", "equipo_key"])

    return df

df = load_data()

if df.empty:
    st.error("El CSV no se está leyendo correctamente.")
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
            x="ratio_titularidad" if "ratio_titularidad" in df.columns else None,
            y="goles_per90",
            size="Minutos" if "Minutos" in df.columns else None,
            color="equipo_key" if "equipo_key" in df.columns else None,
            hover_name="Jugadora",
            template="plotly_white"
        )

        st.plotly_chart(fig, use_container_width=True)

    # 🔥 TOP 10 GOLEADORAS EFICIENTES
    st.markdown("### 🔝 Top 10 Goleadoras Eficientes")

    if "goles_per90" in df.columns and "Minutos" in df.columns:

        df_top = (
            df[df["Minutos"] >= 300]
            .sort_values("goles_per90", ascending=False)
            .head(10)
        )

        cols_show = [c for c in ["Jugadora", "Goles", "goles_per90"] if c in df_top.columns]

        st.dataframe(
            df_top[cols_show].assign(
                goles_per90=lambda x: x["goles_per90"].round(2)
            ),
            use_container_width=True
        )

# =========================================================
# TAB 2 - EQUIPOS
# =========================================================
with tab2:

    if "equipo_key" in df.columns:

        equipos = sorted(df["equipo_key"].unique())
        cols = st.columns(4)

        for i, equipo in enumerate(equipos):
            with cols[i % 4]:
                logo_path = f"{equipo}.png"
                if os.path.exists(logo_path):
                    st.image(logo_path, use_container_width=True)

                if st.button(equipo.upper(), use_container_width=True):
                    st.session_state["equipo_sel"] = equipo

        if "equipo_sel" in st.session_state:
            eq = st.session_state["equipo_sel"]
            df_eq = df[df["equipo_key"] == eq]

            st.markdown(f"### Plantilla {eq.upper()}")

            cols_mostrar = [
                c for c in [
                    "Jugadora",
                    "goles_per90",
                    "amarillas_per90",
                    "Minutos",
                    "ratio_titularidad"
                ] if c in df_eq.columns
            ]

            st.dataframe(
                df_eq[cols_mostrar].sort_values("Minutos", ascending=False),
                use_container_width=True
            )

# =========================================================
# TAB 3 - PERFIL JUGADORA
# =========================================================
with tab3:

    df_filtrado = df.copy()

    # Slider experiencia
    if "experiencia" in df.columns:
        exp_min = int(df["experiencia"].min())
        exp_max = int(df["experiencia"].max())

        exp_range = st.slider(
            "Filtrar por Experiencia",
            exp_min,
            exp_max,
            (exp_min, exp_max)
        )

        df_filtrado = df[
            (df["experiencia"] >= exp_range[0]) &
            (df["experiencia"] <= exp_range[1])
        ]

    if "equipo_key" in df_filtrado.columns and "Jugadora" in df_filtrado.columns:

        eq_choice = st.selectbox("Equipo", sorted(df_filtrado["equipo_key"].unique()))
        df_eq = df_filtrado[df_filtrado["equipo_key"] == eq_choice]

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

# =========================================================
# TAB 4 - PORTERAS
# =========================================================
with tab4:

    if "Posición" in df.columns:

        df_gk = df[df["Posición"].str.contains("Porter", case=False, na=False)]

        if not df_gk.empty:

            if "experiencia" in df_gk.columns:

                exp_min = int(df_gk["experiencia"].min())
                exp_max = int(df_gk["experiencia"].max())

                exp_range = st.slider(
                    "Experiencia (Porteras)",
                    exp_min,
                    exp_max,
                    (exp_min, exp_max),
                    key="gk_slider"
                )

                df_gk = df_gk[
                    (df_gk["experiencia"] >= exp_range[0]) &
                    (df_gk["experiencia"] <= exp_range[1])
                ]

            if "goles_recibidos_per90" in df_gk.columns:

                df_gk = df_gk.sort_values("goles_recibidos_per90", ascending=False)

                st.dataframe(
                    df_gk[[
                        "Jugadora",
                        "experiencia",
                        "goles_recibidos_per90"
                    ]].drop_duplicates(),
                    use_container_width=True
                )
