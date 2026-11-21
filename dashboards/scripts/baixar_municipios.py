import pandas as pd

url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/42/municipios"
municipios = pd.read_json(url)[["id", "nome"]]

municipios["CODIGO"] = municipios["id"].astype(str).str[:6]
municipios = municipios.rename(columns={"nome": "NOME_MUNICIPIO"})[["CODIGO", "NOME_MUNICIPIO"]]

municipios.to_csv("data/auxiliares/municipios_sc.csv", index=False)
print(f"{len(municipios)} municípios salvos")