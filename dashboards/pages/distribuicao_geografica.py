import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from db import PASTA_AUXILIARES, carregar_mapa, dados_filtrados

# ==== Título ====
st.title("Distribuição Geográfica")
st.caption("Onde os pacientes moram, onde são tratados e quanto se deslocam até o tratamento.")

df = dados_filtrados()

# Os itens que comparam municípios usam os dados sem o filtro de município
df_todos_municipios = dados_filtrados(ignorar_municipio=True)
AVISO_MUNICIPIO = "Não é afetado pelo filtro de município de residência."

# ==== Municípios de SC (código e nome) ====
municipios = pd.read_csv(PASTA_AUXILIARES / "municipios_sc.csv", dtype=str)
nomes_municipios = dict(zip(municipios["CODIGO"], municipios["NOME_MUNICIPIO"]))

# ==== Cálculo dos cards ====
perc_tratado_fora = df["TRATADO_FORA_MUNICIPIO"].mean() * 100
perc_diagnosticado_fora = (df["MUNICIPIO_RESIDENCIA"] != df["MUNICIPIO_DIAGNOSTICO"]).mean() * 100

qtd_municipios_trat = df["MUNICIPIO_TRATAMENTO"].nunique()
total_municipios = len(municipios)

# Município que mais realiza tratamentos
casos_por_polo = df["MUNICIPIO_TRATAMENTO"].value_counts()
polo_codigo = casos_por_polo.idxmax()
polo_nome = nomes_municipios.get(polo_codigo, polo_codigo)
perc_polo = casos_por_polo.max() / len(df) * 100

# ==== Cards ====
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    ":material/directions_car: Tratados fora do município de residência",
    f"{perc_tratado_fora:.1f}%".replace(".", ","),
    border=True,
    help="Casos em que o primeiro tratamento foi feito em um município diferente daquele onde o paciente mora.",
)
col2.metric(
    ":material/alt_route: Diagnosticados fora do município de residência",
    f"{perc_diagnosticado_fora:.1f}%".replace(".", ","),
    border=True,
    help="Casos em que o diagnóstico foi feito em um município diferente daquele onde o paciente mora.",
)
col3.metric(
    ":material/map: Municípios que realizam tratamento",
    f"{qtd_municipios_trat} de {total_municipios}",
    border=True,
    help="Municípios de SC com pelo menos um estabelecimento que registrou tratamento oncológico.",
)
col4.metric(
    ":material/hub: Principal polo de tratamento",
    polo_nome,
    border=True,
    help=f"Município que mais realizou tratamentos: {perc_polo:.1f}% do total.".replace(".", ",", 1),
)

# ==== Distância entre a residência e o tratamento ====
def ponto_central(geometria):
    """Devolve a latitude e a longitude do centro de um município do mapa."""
    poligonos = geometria["coordinates"] if geometria["type"] == "MultiPolygon" else [geometria["coordinates"]]
    pontos = [ponto for poligono in poligonos for ponto in poligono[0]]
    latitude = sum(ponto[1] for ponto in pontos) / len(pontos)
    longitude = sum(ponto[0] for ponto in pontos) / len(pontos)
    return latitude, longitude


mapa = carregar_mapa()
centros = {m["properties"]["CODIGO"]: ponto_central(m["geometry"]) for m in mapa["features"]}
latitudes = {codigo: centro[0] for codigo, centro in centros.items()}
longitudes = {codigo: centro[1] for codigo, centro in centros.items()}

# Coordenadas em radianos (residência e tratamento)
lat_resid = np.radians(df["MUNICIPIO_RESIDENCIA"].map(latitudes))
lon_resid = np.radians(df["MUNICIPIO_RESIDENCIA"].map(longitudes))
lat_trat = np.radians(df["MUNICIPIO_TRATAMENTO"].map(latitudes))
lon_trat = np.radians(df["MUNICIPIO_TRATAMENTO"].map(longitudes))

# Distância em linha reta (fórmula de Haversine); 6.371 km é o raio da Terra
parcial = (
    np.sin((lat_trat - lat_resid) / 2) ** 2
    + np.cos(lat_resid) * np.cos(lat_trat) * np.sin((lon_trat - lon_resid) / 2) ** 2
)
df["DISTANCIA_KM"] = 2 * 6371 * np.arcsin(np.sqrt(parcial))

# ==== Casos por faixa de distância até o tratamento ====
with st.container(border=True):
    st.subheader("Distância entre a residência e o tratamento")
    st.caption(
        "Casos por faixa de distância, em linha reta, entre o município onde o paciente mora "
        "e o município onde foi tratado."
    )

    faixas = ["No próprio município", "Até 50 km", "51 a 100 km", "101 a 200 km", "Mais de 200 km"]

    com_distancia = df[df["DISTANCIA_KM"].notna()].copy()
    com_distancia["FAIXA_DISTANCIA"] = pd.cut(
        com_distancia["DISTANCIA_KM"],
        bins=[-1, 0, 50, 100, 200, float("inf")],
        labels=faixas,
    )

    # Sem distância a mostrar (ex: só pacientes de outros estados, fora do mapa de SC)
    if com_distancia.empty:
        st.info("Não há distância a mostrar para pacientes de outros estados.")
    else:
        casos_distancia = (
            com_distancia.groupby("FAIXA_DISTANCIA", observed=False)
            .size()
            .reset_index(name="CASOS")
        )
        casos_distancia["PERCENTUAL"] = casos_distancia["CASOS"] / casos_distancia["CASOS"].sum() * 100

        # Texto em cima de cada barra: "15.230 (51,3%)"
        casos_distancia["TEXTO"] = (
            casos_distancia["CASOS"].map(lambda n: f"{n:,}".replace(",", "."))
            + " ("
            + casos_distancia["PERCENTUAL"].map(lambda p: f"{p:.1f}%".replace(".", ","))
            + ")"
        )

        fig = px.bar(
            casos_distancia,
            x="FAIXA_DISTANCIA",
            y="CASOS",
            text="TEXTO",
            color_discrete_sequence=["#1B59B7"],
            labels={"FAIXA_DISTANCIA": "", "CASOS": "Casos"},
        )
        fig.update_traces(
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>",
        )
        fig.update_yaxes(range=[0, casos_distancia["CASOS"].max() * 1.15])
        fig.update_layout(
            bargap=0.4,
            height=450,
            margin=dict(t=30, b=10, l=10, r=10),
            separators=",.",
            hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
        )
        st.plotly_chart(fig, use_container_width=True)

# ==== Trajetos mais frequentes entre a residência e o tratamento ====
with st.container(border=True):
    titulo, seletor = st.columns([4, 1], vertical_alignment="center")

    qtd_trajetos = seletor.selectbox(
        "Quantidade de trajetos",
        options=[10, 15, 20],
        index=0,
        label_visibility="collapsed",
        key="qtd_trajetos",
    )
    titulo.subheader(f"{qtd_trajetos} trajetos mais frequentes até o tratamento")
    st.caption(
        "Município de residência (esquerda) → município do tratamento (direita). A espessura de cada faixa "
        "é a quantidade de casos. Considera só os casos tratados fora do município de residência."
    )

    # Casos e distância de cada par residência → tratamento
    trajetos = (
        df[df["TRATADO_FORA_MUNICIPIO"] & df["DISTANCIA_KM"].notna()]
        .groupby(["MUNICIPIO_RESIDENCIA", "MUNICIPIO_TRATAMENTO"])
        .agg(CASOS=("DISTANCIA_KM", "size"), KM=("DISTANCIA_KM", "first"))
        .reset_index()
        .nlargest(qtd_trajetos, "CASOS")
    )

    # Sem nenhum caso tratado fora do município (ex: todos trataram na própria cidade)
    if trajetos.empty:
        st.info("Nenhum caso tratado fora do município de residência com os filtros selecionados.")
    else:
        trajetos["ORIGEM"] = trajetos["MUNICIPIO_RESIDENCIA"].map(nomes_municipios)
        trajetos["DESTINO"] = trajetos["MUNICIPIO_TRATAMENTO"].map(nomes_municipios)

        # Nós: residência (esquerda) e tratamento (direita), do maior para o menor
        casos_origem = trajetos.groupby("ORIGEM")["CASOS"].sum().sort_values(ascending=False)
        casos_destino = trajetos.groupby("DESTINO")["CASOS"].sum().sort_values(ascending=False)
        posicao_origem = {nome: i for i, nome in enumerate(casos_origem.index)}
        posicao_destino = {nome: i + len(casos_origem) for i, nome in enumerate(casos_destino.index)}

        # Rótulo de cada nó com os casos (ex: "Palhoça (809)")
        rotulos = [f"{nome} ({casos:,})".replace(",", ".") for nome, casos in casos_origem.items()] + [
            f"{nome} ({casos:,})".replace(",", ".") for nome, casos in casos_destino.items()
        ]
        cores_nos = ["#1B59B7"] * len(casos_origem) + ["#0B3B7B"] * len(casos_destino)

        fig = go.Figure(
            go.Sankey(
                textfont=dict(color="#1F2937", size=13, shadow="none"),
                node=dict(
                    label=rotulos,
                    color=cores_nos,
                    pad=14,
                    thickness=16,
                    hovertemplate="<b>%{label}</b><extra></extra>",
                ),
                link=dict(
                    source=trajetos["ORIGEM"].map(posicao_origem),
                    target=trajetos["DESTINO"].map(posicao_destino),
                    value=trajetos["CASOS"],
                    customdata=trajetos[["ORIGEM", "DESTINO", "KM"]].values,
                    color="rgba(27, 89, 183, 0.30)",
                    hovertemplate=(
                        "<b>%{customdata[0]} → %{customdata[1]}</b><br>"
                        "Casos: %{value:,}<br>"
                        "Distância: %{customdata[2]:.0f} km"
                        "<extra></extra>"
                    ),
                ),
            )
        )
        fig.update_layout(
            height=max(450, len(casos_origem) * 38),
            font_size=13,
            margin=dict(t=10, b=10, l=10, r=10),
            separators=",.",
            hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
        )
        st.plotly_chart(fig, use_container_width=True)

# ==== Polos de tratamento: % de pacientes vindos de outros municípios ====
with st.container(border=True):
    titulo, seletor = st.columns([4, 1], vertical_alignment="center")

    qtd_polos = seletor.selectbox(
        "Quantidade de municípios",
        options=[5, 10, 15],
        index=1,
        label_visibility="collapsed",
        key="qtd_polos_tratamento",
    )
    titulo.subheader("Pacientes vindos de outros municípios nos principais polos de tratamento", help=AVISO_MUNICIPIO)
    st.caption(
        f"Os {qtd_polos} municípios que mais realizam tratamentos. Cada ponto é o percentual dos casos tratados "
        "no município que são de pacientes residentes em outros municípios. "
        "A linha tracejada é o percentual de todo o estado."
    )

    # Os municípios que mais tratam
    top_polos = df_todos_municipios["MUNICIPIO_TRATAMENTO"].value_counts().nlargest(qtd_polos).index

    polos = (
        df_todos_municipios[df_todos_municipios["MUNICIPIO_TRATAMENTO"].isin(top_polos)]
        .groupby("MUNICIPIO_TRATAMENTO")
        .agg(TOTAL=("TRATADO_FORA_MUNICIPIO", "size"), CASOS_FORA=("TRATADO_FORA_MUNICIPIO", "sum"))
        .reset_index()
    )
    polos["PERC_FORA"] = polos["CASOS_FORA"] / polos["TOTAL"] * 100
    polos["POLO"] = polos["MUNICIPIO_TRATAMENTO"].map(nomes_municipios).fillna(polos["MUNICIPIO_TRATAMENTO"])

    # Maior percentual em cima (no eixo do Plotly, o primeiro da lista fica embaixo)
    polos = polos.sort_values("PERC_FORA")

    # Hastes: uma linha de 0 até o ponto de cada município
    hastes_x, hastes_y = [], []
    for polo, perc in zip(polos["POLO"], polos["PERC_FORA"]):
        hastes_x += [0, perc, None]
        hastes_y += [polo, polo, None]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=hastes_x,
            y=hastes_y,
            mode="lines",
            line=dict(color="#BFC9D9", width=3),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=polos["PERC_FORA"],
            y=polos["POLO"],
            mode="markers+text",
            marker=dict(color="#1B59B7", size=14),
            text=polos["PERC_FORA"].map(lambda p: f"{p:.1f}%".replace(".", ",")),
            textposition="middle right",
            customdata=polos[["CASOS_FORA", "TOTAL"]],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Vindos de outros municípios: %{x:.1f}%<br>"
                "%{customdata[0]:,} de %{customdata[1]:,} casos tratados no município"
                "<extra></extra>"
            ),
            showlegend=False,
        )
    )

    # Referência: percentual de todo o estado (sem o filtro de município)
    perc_tratado_fora_estado = df_todos_municipios["TRATADO_FORA_MUNICIPIO"].mean() * 100
    fig.add_vline(
        x=perc_tratado_fora_estado,
        line_dash="dash",
        line_color="#F28C28",
        annotation_text=f"SC: {perc_tratado_fora_estado:.1f}%".replace(".", ","),
        annotation_position="top",
    )

    fig.update_xaxes(range=[0, 108], ticksuffix="%", title="Casos de pacientes vindos de outros municípios")
    fig.update_yaxes(categoryorder="array", categoryarray=polos["POLO"].tolist())
    fig.update_layout(
        height=max(450, qtd_polos * 40),
        margin=dict(t=30, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Abrangência de um município de tratamento ====
with st.container(border=True):
    titulo, seletor = st.columns([3, 2], vertical_alignment="center")

    # Municípios de tratamento, do que mais trata para o que menos trata
    polos_ordenados = df_todos_municipios["MUNICIPIO_TRATAMENTO"].value_counts().index.tolist()
    polo = seletor.selectbox(
        "Município de tratamento",
        options=polos_ordenados,
        format_func=lambda codigo: nomes_municipios.get(codigo, codigo),
        label_visibility="collapsed",
        key="polo_abrangencia",
    )
    polo_nome = nomes_municipios.get(polo, polo)
    titulo.subheader(f"Abrangência de {polo_nome}", help=AVISO_MUNICIPIO)

    # Casos tratados no município escolhido e de onde eles vêm
    casos_polo = df_todos_municipios[df_todos_municipios["MUNICIPIO_TRATAMENTO"] == polo]
    total_polo = len(casos_polo)
    origens = casos_polo["MUNICIPIO_RESIDENCIA"].value_counts()
    perc_vindos_fora = casos_polo["TRATADO_FORA_MUNICIPIO"].mean() * 100
    casos_outros_estados = origens[~origens.index.isin(municipios["CODIGO"])].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("Casos tratados", f"{total_polo:,}".replace(",", "."))
    m2.metric("Municípios de origem", len(origens))
    m3.metric("Vindos de outros municípios", f"{perc_vindos_fora:.1f}%".replace(".", ","))

    legenda = (
        f"Municípios de residência dos pacientes tratados em {polo_nome} (em laranja). "
        f"Os percentuais são calculados sobre os {total_polo:,} casos tratados no município.".replace(",", ".")
    )
    if casos_outros_estados:
        legenda += f" {casos_outros_estados} casos de moradores de outros estados não aparecem no mapa."
    st.caption(legenda)

    # Todos os municípios de SC com a quantidade de casos enviados ao polo (0 se nenhum)
    abrangencia = municipios.rename(columns={"CODIGO": "MUNICIPIO_RESIDENCIA"}).copy()
    abrangencia["CASOS"] = abrangencia["MUNICIPIO_RESIDENCIA"].map(origens).fillna(0).astype(int)
    abrangencia["PERC"] = abrangencia["CASOS"] / total_polo * 100

    # O próprio polo fica fora da escala de cores (senão os moradores dele apagam o resto)
    outros = abrangencia[abrangencia["MUNICIPIO_RESIDENCIA"] != polo]
    proprio = abrangencia[abrangencia["MUNICIPIO_RESIDENCIA"] == polo].assign(DESTAQUE="Município de tratamento")

    fig = px.choropleth(
        outros,
        geojson=mapa,
        locations="MUNICIPIO_RESIDENCIA",
        featureidkey="properties.CODIGO",
        color="CASOS",
        color_continuous_scale="Blues",
        range_color=[0, max(outros["CASOS"].max(), 1)],
        custom_data=["NOME_MUNICIPIO", "PERC"],
        labels={"CASOS": "Casos"},
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Casos: %{z:,}<br>"
            "%{customdata[1]:.2f}% dos casos tratados em " + polo_nome +
            "<extra></extra>"
        ),
    )

    # Camada do polo, em laranja
    destaque = px.choropleth(
        proprio,
        geojson=mapa,
        locations="MUNICIPIO_RESIDENCIA",
        featureidkey="properties.CODIGO",
        color="DESTAQUE",
        color_discrete_map={"Município de tratamento": "#F28C28"},
        custom_data=["NOME_MUNICIPIO", "CASOS", "PERC"],
    )
    destaque.update_traces(
        showlegend=False,
        hovertemplate=(
            "<b>%{customdata[0]}</b> (município de tratamento)<br>"
            "Moradores tratados aqui: %{customdata[1]:,}<br>"
            "%{customdata[2]:.2f}% dos casos tratados em " + polo_nome +
            "<extra></extra>"
        ),
    )
    fig.add_trace(destaque.data[0])

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        height=550,
        margin=dict(t=10, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)