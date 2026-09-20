"""
Fase 3: Redisseny grafic i programacio de la interactivitat

Executar amb:
    streamlit run plot_design.py

Tipologies d'interaccio implementades:
  1. Abstraure/Elaborar: tooltip amb detall complet en passar el ratoli
     per sobre de cada punt (any, estat, font, nominal, real).
  2. Codificar: un toggle que canvia la magnitud representada entre
     euros nominals i euros reals (constants de 2003), en viu.
  3. Filtrar: un rang d'anys seleccionable amb un slider, que permet a
     qui ho consulta reproduir per si mateix la comparacio 2003 vs 2024
     que feia el grafic original d'ERC, pero amb l'eix Y correcte.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

CSV_PATH = "pressupost_generalitat_2003_2024.csv"

st.set_page_config(page_title="Pressupost de la Generalitat, sense mentida visual", layout="wide")


@st.cache_data
def carrega_dades():
    df = pd.read_csv(CSV_PATH)
    df["aprovat"] = df["pressupost_nou_aprovat"].map({"si": "Pressupost nou aprovat", "no": "Prorrogat"})
    df["font_curta"] = df["font"].str.contains("idescat").map(
        {True: "Idescat (no verificat)", False: "API oficial"}
    )
    return df


df = carrega_dades()

st.title("El pressupost de la Generalitat, 2003–2024")
st.caption(
    "Redisseny del grafic publicat per @Esquerra_ERC (30/03/2024), que comparava nomes "
    "2003 i 2024 amb un eix sense escala i un lie factor de aproximadament 2,16. Aquesta versio mostra la "
    "serie completa, amb l'eix a zero i la font de cada dada."
)

# ---------------------------------------------------------------------------
# 3. FILTRAR -- rang d'anys
# ---------------------------------------------------------------------------
any_min, any_max = int(df["any"].min()), int(df["any"].max())
rang = st.slider(
    "Filtra el rang d'anys a comparar",
    min_value=any_min, max_value=any_max, value=(any_min, any_max), step=1,
    help="Prova de posar-lo a 2003–2024 exactament: és la comparació que feia el gràfic original.",
)
df_f = df[(df["any"] >= rang[0]) & (df["any"] <= rang[1])].copy()

# ---------------------------------------------------------------------------
# 2. CODIFICAR -- nominal vs real
# ---------------------------------------------------------------------------
magnitud = st.radio(
    "Magnitud representada",
    ["Euros nominals (any corrent)", "Euros reals (constants de 2003, desflactats per IPC)"],
    horizontal=True,
)
col = "nominal_meur" if magnitud.startswith("Euros nominals") else "real_2003_meur"
etiqueta_y = "Pressupost (M€ nominals)" if col == "nominal_meur" else "Pressupost (M€, constants de 2003)"

# ---------------------------------------------------------------------------
# Grafic (Plotly) -- linia continua + marcadors diferenciats per estat
# ---------------------------------------------------------------------------
fig = go.Figure()

for estat, simbol, mida in [("Pressupost nou aprovat", "circle", 9), ("Prorrogat", "circle-open", 11)]:
    sub = df_f[df_f["aprovat"] == estat]
    fig.add_trace(go.Scatter(
        x=sub["any"], y=sub[col],
        mode="markers",
        name=estat,
        marker=dict(size=mida, symbol=simbol, line=dict(width=2)),
        customdata=sub[["aprovat", "font_curta", "nominal_meur", "real_2003_meur"]],
        hovertemplate=(
            "<b>Any %{x}</b><br>"
            "Estat: %{customdata[0]}<br>"
            "Font: %{customdata[1]}<br>"
            "Nominal: %{customdata[2]:,.2f} M€<br>"
            "Real (2003): %{customdata[3]:,.2f} M€"
            "<extra></extra>"
        ),
    ))

fig.add_trace(go.Scatter(
    x=df_f["any"], y=df_f[col], mode="lines",
    line=dict(width=2, color="rgba(0,61,109,0.55)"),
    name="Evolució", hoverinfo="skip", showlegend=False,
))

fig.update_layout(
    yaxis_title=etiqueta_y,
    xaxis_title="Any",
    yaxis=dict(rangemode="tozero"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    template="simple_white",
    margin=dict(t=60, b=40, l=60, r=20),
    height=520,
)

st.plotly_chart(fig, use_container_width=True)

# Missatge dinamic amb el factor real seleccionat (reforça l'argument de la Fase 1)
if len(df_f) >= 2:
    v0, v1 = df_f[col].iloc[0], df_f[col].iloc[-1]
    st.metric(
        label=f"Increment {rang[0]} → {rang[1]} ({'nominal' if col=='nominal_meur' else 'real, constants 2003'})",
        value=f"×{v1 / v0:.2f}",
    )

st.caption(
    "Passa el ratolí per sobre de qualsevol punt per veure'n l'estat i la font exacta. "
    "Els cercles buits marquen anys amb pressupost prorrogat."
)