import json
import gzip
from geojson_rewind import rewind
from urllib.request import urlopen

url = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/estados/42"
    "?formato=application/vnd.geo+json&intrarregiao=municipio&qualidade=minima"
)

with urlopen(url) as resposta:
    conteudo = gzip.decompress(resposta.read()).decode("utf-8")
    mapa = json.loads(conteudo)

# O IBGE usa código de 7 dígitos; os seus dados usam 6
for municipio in mapa["features"]:
    municipio["properties"]["CODIGO"] = municipio["properties"]["codarea"][:6]

mapa = rewind(mapa, rfc7946=False)
with open("data/auxiliares/mapa_sc.json", "w", encoding="utf-8") as arquivo:
    json.dump(mapa, arquivo, ensure_ascii=False)

print(f"{len(mapa['features'])} municípios no mapa")