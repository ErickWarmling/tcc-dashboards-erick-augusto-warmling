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