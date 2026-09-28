import textwrap
import plotly.express as px
import streamlit as st
import pandas as pd
from db import PASTA_AUXILIARES, carregar_dados, carregar_mapa

df = carregar_dados()

# ==== Título ====
st.title("📊 Visão Geral")
st.caption("Casos oncológicos diagnosticados e tratados em Santa Catarina (jan/2024 a abr/2026)")

# ==== Cálculo dos cards ====
total_casos = len(df)
perc_malignas = (df["CATEGORIA_DIAGNOSTICO"] == "01").mean() * 100
qtd_municipios = df["MUNICIPIO_RESIDENCIA"].nunique()
qtd_hospitais = df["ESTABELECIMENTO_TRATAMENTO"].nunique()

# ==== Cards ====
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total de casos", f"{total_casos:,}".replace(",", "."), border=True)
col2.metric("Neoplasias malignas", f"{perc_malignas:.1f}%".replace(".", ","), border=True)
col3.metric("Municípios de residência", qtd_municipios, border=True)
col4.metric("Estabelecimentos de tratamento", qtd_hospitais, border=True)

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

    fig = px.line(
        casos_mes,
        x="ANO_MES_DIAGNOSTICO",
        y="CASOS",
        markers=True,
        labels={"ANO_MES_DIAGNOSTICO": "Mês", "CASOS": "Casos"},
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Categoria do diagnóstico ====
with graf_dir.container(border=True):
    st.subheader("Categoria do diagnóstico")

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
    fig.update_traces(textinfo="percent")
    fig.update_layout(
        legend=dict(
            orientation="v", 
            yanchor="top", y=-0.05,
            xanchor="center", x=0.5,
        ),
        legend_title_text="",
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Linha 2 de gráficos ====
graf2_esq, graf2_dir = st.columns(2)

# ==== 10 cânceres mais frequentes ====
with graf2_esq.container(border=True):
    st.subheader("10 cânceres mais frequentes")

    top_cids = (
        df.groupby(["DIAGNOSTICO_DETALHADO", "CID_NOME"])
        .size()
        .reset_index(name="CASOS")
        .nlargest(10, "CASOS")
        .sort_values("CASOS")
    )
    top_cids["CANCER"] = top_cids["DIAGNOSTICO_DETALHADO"] + " - " + top_cids["CID_NOME"]

    # Quebra nomes longos em linhas de até 30 letras
    top_cids["CANCER"] = top_cids["CANCER"].apply(lambda nome: "<br>".join(textwrap.wrap(nome, 30)))

    fig = px.bar(
        top_cids,
        x="CASOS",
        y="CANCER",
        orientation="h",
        text="CASOS",
        labels={"CASOS": "Casos", "CANCER": ""},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(range=[0, top_cids["CASOS"].max() * 1.15])
    fig.update_layout(height=550, bargap=0.4, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

# ==== 10 munícipios com mais casos ====
with graf2_dir.container(border=True):
    st.subheader("10 munícipios com mais casos")

    top_municipios = (
        df.groupby("MUNICIPIO_RESIDENCIA_NOME")
        .size()
        .reset_index(name="CASOS")
        .nlargest(10, "CASOS")
        .sort_values("CASOS")
    )

    fig = px.bar(
        top_municipios,
        x="CASOS",
        y="MUNICIPIO_RESIDENCIA_NOME",
        orientation="h",
        text="CASOS",
        labels={"CASOS": "Casos", "MUNICIPIO_RESIDENCIA_NOME": ""},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(range=[0, top_municipios["CASOS"].max() * 1.15])
    st.plotly_chart(fig, use_container_width=True)


# ==== Mapa de casos por município ====
with st.container(border=True):
    st.subheader("Casos por município de residência")

    # Lista com todos os 295 municípios de SC
    todos_municipios = pd.read_csv(PASTA_AUXILIARES / "municipios_sc.csv", dtype=str).rename(
        columns={"CODIGO": "MUNICIPIO_RESIDENCIA", "NOME_MUNICIPIO": "MUNICIPIO_RESIDENCIA_NOME"}
    )

    # Casos de cada município
    contagem = df.groupby("MUNICIPIO_RESIDENCIA").size().reset_index(name="CASOS")

    # Junta: municípios sem casos ficam com 0
    casos_municipio = todos_municipios.merge(contagem, on="MUNICIPIO_RESIDENCIA", how="left")
    casos_municipio["CASOS"] = casos_municipio["CASOS"].fillna(0).astype(int)

    fig = px.choropleth(
        casos_municipio,
        geojson=carregar_mapa(),
        locations="MUNICIPIO_RESIDENCIA",
        featureidkey="properties.CODIGO",
        color="CASOS",
        color_continuous_scale="Blues",
        hover_name="MUNICIPIO_RESIDENCIA_NOME",
        labels={"CASOS": "Casos", "MUNICIPIO_RESIDENCIA": "Código"},
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=550, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)