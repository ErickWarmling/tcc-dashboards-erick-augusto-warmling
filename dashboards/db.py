import os
from pathlib import Path

import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

# Pasta onde estão os dicionários (CIDs e municípios)
PASTA_AUXILIARES = Path(__file__).parent / "data" / "auxiliares"


# ==== Conexão com o banco ====
@st.cache_resource
def get_engine():
    return create_engine(
        f"postgresql+psycopg://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    )


@st.cache_data(ttl=3600)
def consultar(sql: str) -> pd.DataFrame:
    return pd.read_sql(sql, get_engine())


# ==== Traduções simples ====
CATEGORIAS = {
    "01": "Neoplasias Malignas (Lei nº 12.732/12)",
    "02": "Neoplasias in situ",
    "03": "Neoplasias de comportamento incerto ou desconhecido",
    "04": "C44 e C73",
}

SEXOS = {"F": "Feminino", "M": "Masculino"}


# ==== Dados prontos para os dashboards ====
@st.cache_data(ttl=3600)
def carregar_dados() -> pd.DataFrame:
    df = consultar("SELECT * FROM dados_oncologia_sus")

    # ---- Colunas novas ----
    df["FAIXA_ETARIA"] = pd.cut(
        df["IDADE_PACIENTE"],
        bins=[0, 20, 30, 40, 50, 60, 70, 80, 200],
        labels=["0-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"],
        right=False,
    )
    df["ANO_MES_DIAGNOSTICO"] = df["DATA_DIAGNOSTICO"].dt.to_period("M").astype(str)
    df["TRATADO_FORA_MUNICIPIO"] = df["MUNICIPIO_RESIDENCIA"] != df["MUNICIPIO_TRATAMENTO"]

    # ---- Traduções simples ----
    df["CATEGORIA_NOME"] = df["CATEGORIA_DIAGNOSTICO"].map(CATEGORIAS)
    df["SEXO_NOME"] = df["SEXO_PACIENTE"].map(SEXOS)

    # ---- Nome do câncer (CID) ----
    cids = pd.read_csv(
        PASTA_AUXILIARES / "CID-10-CATEGORIAS.CSV",
        sep=";", encoding="latin-1", usecols=["CAT", "DESCRICAO"],
    ).rename(columns={"CAT": "DIAGNOSTICO_DETALHADO", "DESCRICAO": "CID_NOME"})
    df = df.merge(cids, on="DIAGNOSTICO_DETALHADO", how="left")

    # ---- Nome do município de residência ----
    municipios = pd.read_csv(
        PASTA_AUXILIARES / "municipios_sc.csv", dtype=str,
    ).rename(columns={"CODIGO": "MUNICIPIO_RESIDENCIA", "NOME_MUNICIPIO": "MUNICIPIO_RESIDENCIA_NOME"})
    df = df.merge(municipios, on="MUNICIPIO_RESIDENCIA", how="left")

    return df

@st.cache_data
def carregar_mapa() -> dict:
    with open(PASTA_AUXILIARES / "mapa_sc.json", encoding="utf-8") as arquivo:
        return json.load(arquivo)

# ==== Mês por extenso (ex: 2024-01 -> jan/2024) ====
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def nome_mes(ano_mes: str) -> str:
    return f"{MESES[int(ano_mes[5:7]) - 1]}/{ano_mes[:4]}"


# ==== Dados com os filtros do menu lateral aplicados ====
def dados_filtrados(
    ignorar_sexo: bool = False, ignorar_faixa: bool = False, ignorar_municipio: bool = False
) -> pd.DataFrame:
    df = carregar_dados()

    # Período do diagnóstico (ex: 2024-01 a 2025-02)
    periodo = st.session_state.get("filtro_periodo")
    if periodo:
        inicio, fim = periodo
        df = df[df["ANO_MES_DIAGNOSTICO"].between(inicio, fim)]

    # Sexo ("Todos" ou nenhum botão marcado = sem filtro)
    sexo = st.session_state.get("filtro_sexo")
    if sexo and sexo != "Todos" and not ignorar_sexo:
        df = df[df["SEXO_NOME"] == sexo]

    # Faixa etária (nenhuma escolhida = todas)
    faixas_etarias = st.session_state.get("filtro_faixa_etaria")
    if faixas_etarias and not ignorar_faixa:
        df = df[df["FAIXA_ETARIA"].isin(faixas_etarias)]

    # Município de residência (nenhum escolhido = todos)
    municipios_residencia = st.session_state.get("filtro_municipio")
    if municipios_residencia and not ignorar_municipio:
        df = df[df["MUNICIPIO_RESIDENCIA"].isin(municipios_residencia)]

    # Sem casos com os filtros escolhidos: avisa e para a página
    if df.empty:
        st.info(
            "**Nenhum caso encontrado para os filtros selecionados.** "
            "Remova algum filtro ou use o botão **Limpar filtros** no menu lateral."
        )
        st.stop()

    return df.copy()
