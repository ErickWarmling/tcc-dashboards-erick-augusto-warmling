import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

url = "https://apidadosabertos.saude.gov.br/cnes/estabelecimentos"

# ==== Códigos CNES que aparecem no banco (diagnóstico e tratamento) ====
engine = create_engine(
    f"postgresql+psycopg://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
)
codigos = pd.read_sql(
    """
    SELECT "ESTABELECIMENTO_DIAGNOSTICO" AS codigo FROM dados_oncologia_sus
    UNION
    SELECT "ESTABELECIMENTO_TRATAMENTO" AS codigo FROM dados_oncologia_sus
    """,
    engine,
)["codigo"].dropna().astype(str)

# ==== Busca o nome de cada estabelecimento ====
estabelecimentos = []
for codigo in codigos:
    resposta = requests.get(f"{url}/{codigo.lstrip('0')}", timeout=30)

    nome = None
    if resposta.status_code == 200:
        dados = resposta.json()
        nome = dados.get("nome_fantasia") or dados.get("nome_razao_social")

    if nome:
        estabelecimentos.append({"CODIGO": codigo, "NOME_ESTABELECIMENTO": nome})
    else:
        print(f"CNES {codigo} não encontrado")

    time.sleep(0.2)

pd.DataFrame(estabelecimentos).to_csv("data/auxiliares/estabelecimentos.csv", index=False)
print(f"{len(estabelecimentos)} de {len(codigos)} estabelecimentos salvos")