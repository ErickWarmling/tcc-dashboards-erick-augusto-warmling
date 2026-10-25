import textwrap
import plotly.express as px
import streamlit as st
import pandas as pd
from db import PASTA_AUXILIARES, carregar_mapa, dados_filtrados

# ==== Título ====
st.title("Visão Geral")
st.caption("Panorama dos casos oncológicos diagnosticados e tratados em Santa Catarina.")

df = dados_filtrados()

# Os itens que comparam municípios usam os dados sem o filtro de município
df_todos_municipios = dados_filtrados(ignorar_municipio=True)
AVISO_MUNICIPIO = "Não é afetado pelo filtro de município de residência."

# ==== Cálculo dos cards ====
total_casos = len(df)
perc_malignas = (df["CATEGORIA_DIAGNOSTICO"] == "01").mean() * 100
qtd_hospitais = df["ESTABELECIMENTO_TRATAMENTO"].nunique()

# Município de residência com mais casos (só municípios de SC, que têm nome na tabela)
casos_por_municipio = df_todos_municipios["MUNICIPIO_RESIDENCIA_NOME"].value_counts()
municipio_lider = casos_por_municipio.index[0]
casos_lider = casos_por_municipio.iloc[0]
perc_lider = f"{casos_lider / len(df_todos_municipios) * 100:.1f}%".replace(".", ",")
texto_casos_lider = "1 caso" if casos_lider == 1 else f"{casos_lider:,} casos".replace(",", ".")
ajuda_municipio_lider = AVISO_MUNICIPIO

# ==== Cards ====
col1, col2, col3, col4 = st.columns(4)

col1.metric(":material/clinical_notes: Total de casos", f"{total_casos:,}".replace(",", "."), border=True)
col2.metric(
    ":material/oncology: Neoplasias malignas (Lei nº 12.732/12)",
    f"{perc_malignas:.1f}%".replace(".", ","),
    border=True,
    help="CIDs C00 a C97, exceto C44 (pele) e C73 (tireoide), que não são abrangidos pela lei.",
)
col3.metric(
    ":material/location_city: Município com mais casos",
    municipio_lider,
    border=True,
    help=ajuda_municipio_lider,
)
col4.metric(":material/local_hospital: Estabelecimentos de tratamento", qtd_hospitais, border=True)

# ==== Linha 1 de gráficos ====
graf_esq, graf_dir = st.columns([2, 1])

# ==== Casos por mês ====
with graf_esq.container(border=True):
    st.subheader("Casos por mês de diagnóstico")

    casos_mes = (
        df.groupby("ANO_MES_DIAGNOSTICO")
        .size()
        .reset_index(name="CASOS")
    )

    # Mês em português para o hover (ex: jan/2024)
    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    casos_mes["MES_NOME"] = casos_mes["ANO_MES_DIAGNOSTICO"].apply(
        lambda ano_mes: f"{meses[int(ano_mes[5:7]) - 1]}/{ano_mes[:4]}"
    )

    fig = px.line(
        casos_mes,
        x="ANO_MES_DIAGNOSTICO",
        y="CASOS",
        markers=True,
        custom_data=["MES_NOME"],
        labels={"ANO_MES_DIAGNOSTICO": "Mês", "CASOS": "Casos"},
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Casos: %{y:,}"
            "<extra></extra>"
        ),
    )
    fig.update_layout(
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Categoria do diagnóstico ====
with graf_dir.container(border=True):
    st.subheader("Categoria do diagnóstico")
    st.caption("Proporção dos casos em cada categoria de diagnóstico do Painel-Oncologia, conforme a Lei nº 12.732/12.")

    casos_categoria = (
        df.groupby("CATEGORIA_NOME")
        .size()
        .reset_index(name="CASOS")
    )

    fig = px.pie(
        casos_categoria,
        names="CATEGORIA_NOME",
        values="CASOS",
        hole=0.5,
    )
    fig.update_traces(
        textinfo="percent",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Casos: %{value:,}<br>"
            "Proporção: %{percent:.1%} do total"
            "<extra></extra>"
        ),
    )
    fig.update_layout(
        legend=dict(
            orientation="v",
            yanchor="top", y=-0.05,
            xanchor="center", x=0.5,
        ),
        legend_title_text="",
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Linha 2 de gráficos ====
graf2_esq, graf2_dir = st.columns(2)

# ==== Cânceres mais frequentes ====
with graf2_esq.container(border=True):
    titulo, seletor = st.columns([4, 1], vertical_alignment="center")

    qtd_cids = seletor.selectbox(
        "Quantidade de cânceres",
        options=[5, 10],
        index=1,
        label_visibility="collapsed",
        key="qtd_top_cids",
    )
    titulo.subheader(f"{qtd_cids} cânceres mais frequentes")

    top_cids = (
        df.groupby(["DIAGNOSTICO_DETALHADO", "CID_NOME"])
        .size()
        .reset_index(name="CASOS")
        .nlargest(qtd_cids, "CASOS")
        .sort_values("CASOS")
    )
    top_cids["PERC"] = top_cids["CASOS"] / total_casos * 100
    top_cids["CANCER"] = top_cids["DIAGNOSTICO_DETALHADO"] + " - " + top_cids["CID_NOME"]

    # Quebra nomes longos em linhas de até 30 letras
    top_cids["CANCER"] = top_cids["CANCER"].apply(lambda nome: "<br>".join(textwrap.wrap(nome, 30)))

    fig = px.bar(
        top_cids,
        x="CASOS",
        y="CANCER",
        orientation="h",
        text="CASOS",
        custom_data=["PERC"],
        labels={"CASOS": "Casos", "CANCER": ""},
    )
    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
                texttemplate="%{x:,} (%{customdata[0]:.1f}%)",

        hovertemplate=(
            "<b>%{y}</b><br>"
            "Casos: %{x:,}<br>"
            "Percentual: %{customdata[0]:.1f}% do total"
            "<extra></extra>"
        ),
    )
    fig.update_xaxes(range=[0, top_cids["CASOS"].max() * 1.3])
    fig.update_layout(
        height=550,
        bargap=0.4,
        margin=dict(t=10, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Municípios com mais casos ====
with graf2_dir.container(border=True):
    titulo, seletor = st.columns([4, 1], vertical_alignment="center")

    qtd = seletor.selectbox(
        "Quantidade de municípios",
        options=[5, 10, 15, 20],
        index=1,
        label_visibility="collapsed",
        key="qtd_top_municipios",
    )
    titulo.subheader(f"{qtd} municípios com mais casos", help=AVISO_MUNICIPIO)
    st.caption("Municípios de residência dos pacientes com mais casos e o percentual de cada um sobre o total.")

    top_municipios = (
        df_todos_municipios.groupby("MUNICIPIO_RESIDENCIA_NOME")
        .size()
        .reset_index(name="CASOS")
        .nlargest(qtd, "CASOS")
        .sort_values("CASOS")
    )
    top_municipios["PERC"] = top_municipios["CASOS"] / len(df_todos_municipios) * 100

    fig = px.bar(
        top_municipios,
        x="CASOS",
        y="MUNICIPIO_RESIDENCIA_NOME",
        orientation="h",
        text="CASOS",
        custom_data=["PERC"],
        labels={"CASOS": "Casos", "MUNICIPIO_RESIDENCIA_NOME": ""},
    )
    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        texttemplate="%{x:,} (%{customdata[0]:.1f}%)",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Casos: %{x:,}<br>"
            "Percentual: %{customdata[0]:.1f}% do total"
            "<extra></extra>"
        ),
    )
    fig.update_xaxes(range=[0, top_municipios["CASOS"].max() * 1.3])
    fig.update_layout(
        height=550,
        bargap=0.4,
        margin=dict(t=10, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Mapa de casos por município ====
with st.container(border=True):
    st.subheader("Casos por município de residência", help=AVISO_MUNICIPIO)

    # Lista com todos os 295 municípios de SC
    todos_municipios = pd.read_csv(PASTA_AUXILIARES / "municipios_sc.csv", dtype=str).rename(
        columns={"CODIGO": "MUNICIPIO_RESIDENCIA", "NOME_MUNICIPIO": "MUNICIPIO_RESIDENCIA_NOME"}
    )

    # Casos de cada município
    contagem = df_todos_municipios.groupby("MUNICIPIO_RESIDENCIA").size().reset_index(name="CASOS")

    # Junta: municípios sem casos ficam com 0
    casos_municipio = todos_municipios.merge(contagem, on="MUNICIPIO_RESIDENCIA", how="left")
    casos_municipio["CASOS"] = casos_municipio["CASOS"].fillna(0).astype(int)
    casos_municipio["PERC"] = casos_municipio["CASOS"] / len(df_todos_municipios) * 100

    fig = px.choropleth(
        casos_municipio,
        geojson=carregar_mapa(),
        locations="MUNICIPIO_RESIDENCIA",
        featureidkey="properties.CODIGO",
        color="CASOS",
        color_continuous_scale="Blues",
        custom_data=["MUNICIPIO_RESIDENCIA_NOME", "PERC"],
        labels={"CASOS": "Casos"},
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Casos: %{z:,}<br>"
            "Percentual: %{customdata[1]:.1f}% do total"
            "<extra></extra>"
        ),
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        height=550,
        margin=dict(t=10, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)