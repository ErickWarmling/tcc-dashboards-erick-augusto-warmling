import textwrap
import pandas as pd
import plotly.express as px
import streamlit as st
from db import PASTA_AUXILIARES, dados_filtrados

# ==== Título ====
st.title("Diagnósticos")
st.caption("Tipos de câncer diagnosticados, a rede de estabelecimentos que realiza os diagnósticos e o tempo até o início do tratamento.")

df = dados_filtrados()

# ==== Cálculo dos cards ====
qtd_cids = df["DIAGNOSTICO_DETALHADO"].nunique()

qtd_municipios_diag = df["MUNICIPIO_DIAGNOSTICO"].nunique()
total_municipios = len(pd.read_csv(PASTA_AUXILIARES / "municipios_sc.csv", dtype=str))

# Dias entre o diagnóstico e o primeiro tratamento
df["DIAS_ATE_TRATAMENTO"] = (df["DATA_TRATAMENTO"] - df["DATA_DIAGNOSTICO"]).dt.days

# Prazo de 60 dias: só vale para a categoria 01 (abrangida pela lei)
dias_malignas = df.loc[df["CATEGORIA_DIAGNOSTICO"] == "01", "DIAS_ATE_TRATAMENTO"].dropna()
perc_ate_60 = (dias_malignas <= 60).mean() * 100

qtd_estab_diag = df["ESTABELECIMENTO_DIAGNOSTICO"].nunique()

# ==== Cards ====
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    ":material/microbiology: Tipos de câncer diagnosticados",
    qtd_cids,
    border=True,
    help="Quantidade de códigos CID-10 diferentes registrados nos diagnósticos.",
)
col2.metric(
    ":material/location_on: Municípios com serviço de diagnóstico",
    f"{qtd_municipios_diag} de {total_municipios}",
    border=True,
    help="Municípios de SC com pelo menos um estabelecimento que registrou diagnóstico.",
)
col3.metric(
    ":material/timer: Tratados em até 60 dias",
    f"{perc_ate_60:.1f}%".replace(".", ","),
    border=True,
    help="Casos de neoplasia maligna (Lei nº 12.732/12) que iniciaram o tratamento em até 60 dias após o diagnóstico.",
)
col4.metric(":material/lab_research: Estabelecimentos de diagnóstico", qtd_estab_diag, border=True)

# ==== Grupos da CID-10 (região do corpo) ====
# (letra, número inicial, número final, nome do grupo)
GRUPOS_CID = [
    ("C", 0, 14, "Lábio, cavidade oral e faringe"),
    ("C", 15, 26, "Órgãos digestivos"),
    ("C", 30, 39, "Aparelho respiratório e órgãos intratorácicos"),
    ("C", 40, 41, "Ossos e cartilagens articulares"),
    ("C", 43, 44, "Pele"),
    ("C", 45, 49, "Tecido mesotelial e tecidos moles"),
    ("C", 50, 50, "Mama"),
    ("C", 51, 58, "Órgãos genitais femininos"),
    ("C", 60, 63, "Órgãos genitais masculinos"),
    ("C", 64, 68, "Trato urinário"),
    ("C", 69, 72, "Olhos, encéfalo e sistema nervoso central"),
    ("C", 73, 75, "Tireoide e outras glândulas endócrinas"),
    ("C", 76, 80, "Localizações mal definidas, secundárias e não especificadas"),
    ("C", 81, 96, "Tecido linfático e hematopoético"),
    ("C", 97, 97, "Localizações múltiplas independentes"),
    ("D", 0, 9, "Neoplasias in situ"),
    ("D", 37, 48, "Comportamento incerto ou desconhecido"),
]

def grupo_cid(cid):
    """Devolve o grupo da CID-10 a que o código pertence (ex: C50 -> Mama)."""
    letra, numero = cid[0], int(cid[1:3])
    for letra_grupo, inicio, fim, nome in GRUPOS_CID:
        if letra == letra_grupo and inicio <= numero <= fim:
            return nome
    return "Outros"


# ==== Composição dos diagnósticos ====
with st.container(border=True):
    st.subheader("Composição dos diagnósticos")
    st.caption("Tipos de câncer agrupados pela região do corpo (grupos da CID-10). Clique em um grupo para ampliar.")

    casos_cid = (
        df.groupby(["DIAGNOSTICO_DETALHADO", "CID_NOME"])
        .size()
        .reset_index(name="CASOS")
    )
    casos_cid["GRUPO"] = casos_cid["DIAGNOSTICO_DETALHADO"].apply(grupo_cid)
    casos_cid["CANCER"] = casos_cid["DIAGNOSTICO_DETALHADO"] + " - " + casos_cid["CID_NOME"]

    # Quebra nomes longos em linhas de até 25 letras
    casos_cid["CANCER"] = casos_cid["CANCER"].apply(lambda nome: "<br>".join(textwrap.wrap(nome, 25)))

    fig = px.treemap(
        casos_cid,
        path=["GRUPO", "CANCER"],
        values="CASOS",
        color="GRUPO",
    )
    fig.update_traces(
        texttemplate="%{label}<br>%{value:,} (%{percentRoot:.1%})",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Casos: %{value:,}<br>"
            "Percentual: %{percentRoot:.1%} do total"
            "<extra></extra>"
        ),
    )
    fig.update_layout(
        height=650,
        margin=dict(t=10, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Evolução mensal dos principais tipos de câncer ====
with st.container(border=True):
    titulo, seletor = st.columns([4, 1], vertical_alignment="center")

    qtd_linhas = seletor.selectbox(
        "Quantidade de cânceres",
        options=[3, 5, 8],
        index=1,
        label_visibility="collapsed",
        key="qtd_evolucao_cids",
    )
    titulo.subheader(f"Evolução mensal dos {qtd_linhas} cânceres mais frequentes")

    # Os cânceres mais frequentes no período todo
    top_cids = df["DIAGNOSTICO_DETALHADO"].value_counts().nlargest(qtd_linhas).index

    evolucao = (
        df[df["DIAGNOSTICO_DETALHADO"].isin(top_cids)]
        .groupby(["ANO_MES_DIAGNOSTICO", "DIAGNOSTICO_DETALHADO", "CID_NOME"])
        .size()
        .reset_index(name="CASOS")
    )
    evolucao["CANCER"] = evolucao["DIAGNOSTICO_DETALHADO"] + " - " + evolucao["CID_NOME"]

    # Mês em português para o hover (ex: jan/2024)
    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    evolucao["MES_NOME"] = evolucao["ANO_MES_DIAGNOSTICO"].apply(
        lambda ano_mes: f"{meses[int(ano_mes[5:7]) - 1]}/{ano_mes[:4]}"
    )

    # Legenda na ordem do câncer mais frequente para o menos frequente
    ordem = evolucao.groupby("CANCER")["CASOS"].sum().sort_values(ascending=False).index.tolist()

    fig = px.line(
        evolucao,
        x="ANO_MES_DIAGNOSTICO",
        y="CASOS",
        color="CANCER",
        markers=True,
        custom_data=["MES_NOME"],
        category_orders={"CANCER": ordem},
        labels={"ANO_MES_DIAGNOSTICO": "Mês", "CASOS": "Casos", "CANCER": ""},
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{fullData.name}</b><br>"
            "%{customdata[0]}<br>"
            "Casos: %{y:,}"
            "<extra></extra>"
        ),
    )
    fig.update_layout(
        height=550,
        legend=dict(orientation="v", yanchor="top", y=-0.2, xanchor="left", x=0),
        margin=dict(t=10, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Tempo até o tratamento por tipo de câncer ====
with st.container(border=True):
    st.subheader("Tempo até o tratamento por tipo de câncer")
    st.caption(
        "Proporção dos casos em cada faixa de tempo entre o diagnóstico e o primeiro tratamento, "
        "nos 10 tipos de câncer mais frequentes. Faixas da nota técnica do Painel-Oncologia."
    )

    # Os 10 cânceres mais frequentes, só com os casos que têm as duas datas
    top10_cids = df["DIAGNOSTICO_DETALHADO"].value_counts().nlargest(10).index
    tempo_cancer = df[
        df["DIAGNOSTICO_DETALHADO"].isin(top10_cids) & df["DIAS_ATE_TRATAMENTO"].notna()
    ].copy()

    # Faixas de tempo (laudo posterior ao tratamento entra em 0 a 30 dias)
    faixas = ["0 a 30 dias", "31 a 60 dias", "Mais de 60 dias"]
    tempo_cancer["FAIXA_TEMPO"] = pd.cut(
        tempo_cancer["DIAS_ATE_TRATAMENTO"],
        bins=[float("-inf"), 30, 60, float("inf")],
        labels=faixas,
    )

    tempo_cancer["CANCER"] = tempo_cancer["DIAGNOSTICO_DETALHADO"] + " - " + tempo_cancer["CID_NOME"]
    tempo_cancer["CANCER"] = tempo_cancer["CANCER"].apply(lambda nome: "<br>".join(textwrap.wrap(nome, 30)))

    faixa_cancer = (
        tempo_cancer.groupby(["CANCER", "FAIXA_TEMPO"], observed=False)
        .size()
        .reset_index(name="CASOS")
    )

    # Percentual de cada faixa dentro do câncer (cada barra soma 100%)
    total_cancer = faixa_cancer.groupby("CANCER")["CASOS"].transform("sum")
    faixa_cancer["PERCENTUAL"] = faixa_cancer["CASOS"] / total_cancer * 100

    # Ordena pelo percentual acima de 60 dias (maior espera em cima)
    ordem = (
        faixa_cancer[faixa_cancer["FAIXA_TEMPO"] == "Mais de 60 dias"]
        .sort_values("PERCENTUAL", ascending=False)["CANCER"]
        .tolist()
    )

    fig = px.bar(
        faixa_cancer,
        x="PERCENTUAL",
        y="CANCER",
        color="FAIXA_TEMPO",
        orientation="h",
        custom_data=["CASOS"],
        category_orders={"CANCER": ordem, "FAIXA_TEMPO": faixas},
        color_discrete_map={
            "0 a 30 dias": "#2E9E5B",
            "31 a 60 dias": "#F28C28",
            "Mais de 60 dias": "#C0392B",
        },
        labels={"PERCENTUAL": "% dos casos", "CANCER": "", "FAIXA_TEMPO": ""},
    )
    fig.update_traces(
        texttemplate="%{x:.1f}%",
        textposition="inside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "%{fullData.name}: %{x:.1f}% (%{customdata[0]:,} casos)"
            "<extra></extra>"
        ),
    )
    fig.update_xaxes(range=[0, 100], ticksuffix="%")
    fig.update_layout(
        barmode="stack",
        bargap=0.3,
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(t=30, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Linha de gráficos da rede de diagnóstico ====
graf_esq, graf_dir = st.columns(2)

# ==== Tempo até o tratamento conforme o local ====
with graf_esq.container(border=True):
    st.subheader("Tempo até o tratamento conforme o local")
    st.caption(
        "Tempo mediano entre o diagnóstico e o primeiro tratamento quando o tratamento é feito no mesmo "
        "estabelecimento do diagnóstico, em outro estabelecimento do mesmo município ou em outro município."
    )

    local = df[df["DIAS_ATE_TRATAMENTO"].notna()].copy()

    # Laudo posterior ao tratamento conta como 0 dia
    local["DIAS"] = local["DIAS_ATE_TRATAMENTO"].clip(lower=0)

    # Onde o tratamento foi feito em relação ao diagnóstico
    locais = ["Mesmo estabelecimento", "Outro estabelecimento,<br>mesmo município", "Outro município"]
    local["LOCAL"] = locais[2]
    local.loc[local["MUNICIPIO_DIAGNOSTICO"] == local["MUNICIPIO_TRATAMENTO"], "LOCAL"] = locais[1]
    local.loc[local["ESTABELECIMENTO_DIAGNOSTICO"] == local["ESTABELECIMENTO_TRATAMENTO"], "LOCAL"] = locais[0]

    tempo_local = (
        local.groupby("LOCAL")
        .agg(MEDIANA=("DIAS", "median"), CASOS=("DIAS", "size"))
        .reset_index()
    )
    tempo_local["PERC"] = tempo_local["CASOS"] / tempo_local["CASOS"].sum() * 100

    fig = px.bar(
        tempo_local,
        x="LOCAL",
        y="MEDIANA",
        text="MEDIANA",
        custom_data=["CASOS", "PERC"],
        category_orders={"LOCAL": locais},
        color_discrete_sequence=["#1B59B7"],
        labels={"LOCAL": "", "MEDIANA": "Tempo mediano (dias)"},
    )
    fig.update_traces(
        texttemplate="%{y:.0f} dias",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Tempo mediano: %{y:.0f} dias<br>"
            "Casos: %{customdata[0]:,} (%{customdata[1]:.1f}% do total)"
            "<extra></extra>"
        ),
    )
    fig.update_yaxes(range=[0, tempo_local["MEDIANA"].max() * 1.15])
    fig.update_layout(
        bargap=0.5,
        height=450,
        margin=dict(t=30, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Estabelecimentos que mais diagnosticam ====
with graf_dir.container(border=True):
    titulo, seletor = st.columns([4, 1], vertical_alignment="center")

    qtd_estab = seletor.selectbox(
        "Quantidade de estabelecimentos",
        options=[5, 10, 15],
        index=1,
        label_visibility="collapsed",
        key="qtd_top_estab_diag",
    )
    titulo.subheader(f"{qtd_estab} estabelecimentos que mais diagnosticam")
    st.caption(
        "Estabelecimentos, pelo nome cadastrado no CNES, que registraram mais diagnósticos "
        "e o percentual de cada um sobre o total."
    )

    top_estab = (
        df.groupby(["ESTABELECIMENTO_DIAGNOSTICO", "MUNICIPIO_DIAGNOSTICO"])
        .size()
        .reset_index(name="CASOS")
        .nlargest(qtd_estab, "CASOS")
        .sort_values("CASOS")
    )
    top_estab["PERC"] = top_estab["CASOS"] / len(df) * 100

    # Nome do município do estabelecimento
    municipios = pd.read_csv(PASTA_AUXILIARES / "municipios_sc.csv", dtype=str).rename(
        columns={"CODIGO": "MUNICIPIO_DIAGNOSTICO", "NOME_MUNICIPIO": "MUNICIPIO_NOME"}
    )
    top_estab = top_estab.merge(municipios, on="MUNICIPIO_DIAGNOSTICO", how="left")
    top_estab["MUNICIPIO_NOME"] = top_estab["MUNICIPIO_NOME"].fillna("Fora de SC")

    # Nome do estabelecimento (se não tiver nome, mostra o código CNES)
    nomes = pd.read_csv(PASTA_AUXILIARES / "estabelecimentos.csv", dtype=str).rename(
        columns={"CODIGO": "ESTABELECIMENTO_DIAGNOSTICO"}
    )
    top_estab = top_estab.merge(nomes, on="ESTABELECIMENTO_DIAGNOSTICO", how="left")
    top_estab["ESTABELECIMENTO"] = top_estab["NOME_ESTABELECIMENTO"].fillna(
        "CNES " + top_estab["ESTABELECIMENTO_DIAGNOSTICO"]
    ) + " (" + top_estab["MUNICIPIO_NOME"] + ")"

    # Quebra nomes longos em linhas de até 30 letras
    top_estab["ESTABELECIMENTO"] = top_estab["ESTABELECIMENTO"].apply(
        lambda nome: "<br>".join(textwrap.wrap(nome, 30))
    )

    fig = px.bar(
        top_estab,
        x="CASOS",
        y="ESTABELECIMENTO",
        orientation="h",
        text="CASOS",
        custom_data=["PERC", "ESTABELECIMENTO_DIAGNOSTICO", "MUNICIPIO_NOME"],
        color_discrete_sequence=["#1B59B7"],
        labels={"CASOS": "Casos", "ESTABELECIMENTO": ""},
    )
    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        texttemplate="%{x:,} (%{customdata[0]:.1f}%)",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "CNES: %{customdata[1]}<br>"
            "Município: %{customdata[2]}<br>"
            "Casos: %{x:,}<br>"
            "Percentual: %{customdata[0]:.1f}% do total"
            "<extra></extra>"
        ),
    )
    fig.update_xaxes(range=[0, top_estab["CASOS"].max() * 1.45])
    fig.update_layout(
        height=max(450, qtd_estab * 50),
        bargap=0.4,
        margin=dict(t=10, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)