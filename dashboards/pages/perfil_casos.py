import textwrap
import plotly.express as px
import streamlit as st
from db import dados_filtrados

# ==== Título ====
st.title("Perfil dos Casos")
st.caption("Idade e sexo dos pacientes e os cânceres mais frequentes em cada grupo.")

df = dados_filtrados()

# Os itens que comparam sexos ou idades usam os dados sem o filtro da variável comparada
df_ambos_sexos = dados_filtrados(ignorar_sexo=True)
df_todas_faixas = dados_filtrados(ignorar_faixa=True)
df_sem_sexo_faixa = dados_filtrados(ignorar_sexo=True, ignorar_faixa=True)
AVISO_SEXO = "Não é afetado pelo filtro de sexo."
AVISO_FAIXA = "Não é afetado pelo filtro de faixa etária."
AVISO_SEXO_FAIXA = "Não é afetado pelos filtros de sexo e faixa etária."

# ==== Cálculo dos cards ====
idade_media = df["IDADE_PACIENTE"].mean()
perc_masculino = (df_ambos_sexos["SEXO_PACIENTE"] == "M").mean() * 100
perc_feminino = (df_ambos_sexos["SEXO_PACIENTE"] == "F").mean() * 100
faixa_predominante = df_todas_faixas["FAIXA_ETARIA"].value_counts().idxmax()

# ==== Cards ====
col1, col2, col3, col4 = st.columns(4)

col1.metric(":material/cake: Idade média", f"{idade_media:.1f} anos".replace(".", ","), border=True)
col2.metric(":material/male: Masculino", f"{perc_masculino:.1f}%".replace(".", ","), border=True, help=AVISO_SEXO)
col3.metric(":material/female: Feminino", f"{perc_feminino:.1f}%".replace(".", ","), border=True, help=AVISO_SEXO)
col4.metric(":material/family_restroom: Faixa etária predominante", f"{faixa_predominante} anos", border=True, help=AVISO_FAIXA)

# ==== Linha 1 de gráficos ====
graf_esq, graf_dir = st.columns(2)

# ==== Pirâmide etária ====
with graf_esq.container(border=True):
    st.subheader("Pirâmide etária", help=AVISO_SEXO_FAIXA)
    st.caption("Casos em cada faixa etária, com o sexo masculino à esquerda e o feminino à direita.")

    piramide = (
        df_sem_sexo_faixa.groupby(["FAIXA_ETARIA", "SEXO_NOME"], observed=False)
        .size()
        .reset_index(name="CASOS")
    )

    # Homens ficam com valor negativo para as barras irem para a esquerda
    piramide["CASOS_GRAFICO"] = piramide["CASOS"].where(
        piramide["SEXO_NOME"] == "Feminino", -piramide["CASOS"]
    )

    # Percentual de cada barra sobre o total de casos da pirâmide
    piramide["PERCENTUAL"] = piramide["CASOS"] / piramide["CASOS"].sum() * 100

    fig = px.bar(
        piramide,
        x="CASOS_GRAFICO",
        y="FAIXA_ETARIA",
        color="SEXO_NOME",
        orientation="h",
        custom_data=["CASOS", "PERCENTUAL"],
        color_discrete_map={"Masculino": "#1B59B7", "Feminino": "#E26D9A"},
        labels={"CASOS_GRAFICO": "Casos", "FAIXA_ETARIA": "Faixa etária", "SEXO_NOME": ""},
    )

    # Mostra os números sempre positivos no eixo e ao passar o mouse
    maximo = piramide["CASOS"].max()
    marcas = [-maximo, -maximo // 2, 0, maximo // 2, maximo]
    fig.update_xaxes(
        tickvals=marcas,
        ticktext=[f"{abs(m):,}".replace(",", ".") for m in marcas],
        range=[-maximo * 1.1, maximo * 1.1],
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{fullData.name} · %{y} anos</b><br>"
            "Casos: %{customdata[0]:,}<br>"
            "Percentual: %{customdata[1]:.1f}% do total"
            "<extra></extra>"
        ),
    )
    fig.update_layout(
        barmode="relative",
        bargap=0.1,
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(t=30, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Distribuição dos casos por sexo ====
with graf_dir.container(border=True):
    st.subheader("Distribuição dos casos por sexo", help=AVISO_SEXO)

    casos_sexo = (
        df_ambos_sexos.groupby("SEXO_NOME")
        .size()
        .reset_index(name="CASOS")
    )
    casos_sexo["PERCENTUAL"] = casos_sexo["CASOS"] / casos_sexo["CASOS"].sum() * 100

    # Texto em cima de cada barra: "15.230 (51,3%)"
    casos_sexo["TEXTO"] = (
        casos_sexo["CASOS"].map(lambda n: f"{n:,}".replace(",", "."))
        + " ("
        + casos_sexo["PERCENTUAL"].map(lambda p: f"{p:.1f}%".replace(".", ","))
        + ")"
    )

    fig = px.bar(
        casos_sexo,
        x="SEXO_NOME",
        y="CASOS",
        color="SEXO_NOME",
        text="TEXTO",
        custom_data=["PERCENTUAL"],
        color_discrete_map={"Masculino": "#1B59B7", "Feminino": "#E26D9A"},
        labels={"SEXO_NOME": "", "CASOS": "Casos"},
    )
    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Casos: %{y:,}<br>"
            "Percentual: %{customdata[0]:.1f}% do total"
            "<extra></extra>"
        ),
    )
    fig.update_yaxes(range=[0, casos_sexo["CASOS"].max() * 1.15])
    fig.update_layout(
        showlegend=False,
        bargap=0.65,
        height=450,
        margin=dict(t=30, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Linha 2 de gráficos ====
graf2_esq, graf2_dir = st.columns(2)

# ==== Distribuição da idade ====
with graf2_esq.container(border=True):
    st.subheader("Distribuição da idade", help=AVISO_FAIXA)
    st.caption("Quantidade de casos por idade no diagnóstico. A linha tracejada marca a idade média.")

    # Casos em cada idade (uma barra por ano de idade)
    casos_idade = df_todas_faixas.groupby("IDADE_PACIENTE").size().reset_index(name="CASOS")
    casos_idade["PERCENTUAL"] = casos_idade["CASOS"] / casos_idade["CASOS"].sum() * 100

    fig = px.bar(
        casos_idade,
        x="IDADE_PACIENTE",
        y="CASOS",
        custom_data=["PERCENTUAL"],
        color_discrete_sequence=["#1B59B7"],
        labels={"IDADE_PACIENTE": "Idade no diagnóstico (anos)", "CASOS": "Casos"},
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{x} anos</b><br>"
            "Casos: %{y:,}<br>"
            "Percentual: %{customdata[0]:.1f}% do total"
            "<extra></extra>"
        ),
    )

    # Linha tracejada na idade média (das mesmas idades mostradas no histograma)
    idade_media_histograma = df_todas_faixas["IDADE_PACIENTE"].mean()
    fig.add_vline(
        x=idade_media_histograma,
        line_dash="dash",
        line_color="#F28C28",
        annotation_text=f"Média: {idade_media_histograma:.1f} anos".replace(".", ","),
        annotation_position="top left",
    )

    fig.update_layout(
        yaxis_title="Casos",
        bargap=0.05,
        height=450,
        margin=dict(t=30, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Faixa etária × categoria do diagnóstico ====
with graf2_dir.container(border=True):
    st.subheader("Faixa etária × categoria do diagnóstico", help=AVISO_FAIXA)
    st.caption("Em cada faixa etária, a proporção dos casos em cada categoria de diagnóstico. Cada coluna soma 100%.")

    faixa_categoria = (
        df_todas_faixas.groupby(["FAIXA_ETARIA", "CATEGORIA_NOME"], observed=False)
        .size()
        .reset_index(name="CASOS")
    )

    # Percentual de cada categoria dentro da faixa etária (cada coluna soma 100%)
    total_faixa = faixa_categoria.groupby("FAIXA_ETARIA", observed=False)["CASOS"].transform("sum")
    faixa_categoria["PERCENTUAL"] = faixa_categoria["CASOS"] / total_faixa * 100

    fig = px.bar(
        faixa_categoria,
        x="FAIXA_ETARIA",
        y="PERCENTUAL",
        color="CATEGORIA_NOME",
        custom_data=["CASOS"],
        color_discrete_map={
            "Neoplasias Malignas (Lei nº 12.732/12)": "#1B59B7",
            "Neoplasias in situ": "#2E9E5B",
            "Neoplasias de comportamento incerto ou desconhecido": "#F28C28",
            "C44 e C73": "#8E6BBF",
        },
        labels={"FAIXA_ETARIA": "Faixa etária", "PERCENTUAL": "% dos casos", "CATEGORIA_NOME": ""},
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{fullData.name}</b><br>"
            "Faixa etária: %{x} anos<br>"
            "Casos: %{customdata[0]:,}<br>"
            "Percentual: %{y:.1f}% dos casos da faixa"
            "<extra></extra>"
        ),
    )
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    fig.update_layout(
        barmode="stack",
        bargap=0.2,
        height=450,
        legend=dict(orientation="v", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=30, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)


# ==== Principais tipos de câncer por sexo ====
def grafico_principais_canceres(dados, cor, sexo):
    """Barras deitadas com os 10 cânceres mais frequentes."""
    top_cids = (
        dados.groupby(["DIAGNOSTICO_DETALHADO", "CID_NOME"])
        .size()
        .reset_index(name="CASOS")
        .nlargest(10, "CASOS")
        .sort_values("CASOS")
    )
    top_cids["CANCER"] = top_cids["DIAGNOSTICO_DETALHADO"] + " - " + top_cids["CID_NOME"]
    top_cids["CANCER"] = top_cids["CANCER"].apply(lambda nome: "<br>".join(textwrap.wrap(nome, 30)))

    # Percentual sobre todos os casos do sexo
    top_cids["PERC"] = top_cids["CASOS"] / len(dados) * 100

    fig = px.bar(
        top_cids,
        x="CASOS",
        y="CANCER",
        orientation="h",
        custom_data=["PERC"],
        color_discrete_sequence=[cor],
        labels={"CASOS": "Casos", "CANCER": ""},
    )
    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        texttemplate="%{x:,} (%{customdata[0]:.1f}%)",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Casos: %{x:,}<br>"
            "Percentual: %{customdata[0]:.1f}% dos casos do sexo " + sexo +
            "<extra></extra>"
        ),
    )
    fig.update_xaxes(range=[0, top_cids["CASOS"].max() * 1.35])
    fig.update_layout(
        height=550,
        bargap=0.4,
        margin=dict(t=10, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    return fig


with st.container(border=True):
    st.subheader("Principais tipos de câncer por sexo", help=AVISO_SEXO)

    col_masc, col_fem = st.columns(2)

    with col_masc:
        st.markdown("**Masculino**")
        casos_masc = df_ambos_sexos[df_ambos_sexos["SEXO_PACIENTE"] == "M"]
        st.plotly_chart(grafico_principais_canceres(casos_masc, "#1B59B7", "masculino"), use_container_width=True)

    with col_fem:
        st.markdown("**Feminino**")
        casos_fem = df_ambos_sexos[df_ambos_sexos["SEXO_PACIENTE"] == "F"]
        st.plotly_chart(grafico_principais_canceres(casos_fem, "#E26D9A", "feminino"), use_container_width=True)


# ==== Idade × tipo de câncer ====
with st.container(border=True):
    titulo, seletor = st.columns([3, 2], vertical_alignment="center")

    categoria = seletor.selectbox(
        "Categoria do diagnóstico",
        options=["Todas as categorias"] + sorted(df_todas_faixas["CATEGORIA_NOME"].dropna().unique()),
        label_visibility="collapsed",
        key="categoria_idade_cancer",
    )
    titulo.subheader("Idade × tipo de câncer", help=AVISO_FAIXA)

    # Filtra a categoria escolhida
    dados_categoria = (
        df_todas_faixas
        if categoria == "Todas as categorias"
        else df_todas_faixas[df_todas_faixas["CATEGORIA_NOME"] == categoria]
    )

    # Os 10 cânceres mais frequentes dentro da categoria
    top10_cids = dados_categoria["DIAGNOSTICO_DETALHADO"].value_counts().nlargest(10).index
    idades_cancer = dados_categoria[dados_categoria["DIAGNOSTICO_DETALHADO"].isin(top10_cids)].copy()

    st.caption(
        f"Percentual dos casos de cada câncer em cada faixa etária, nos {len(top10_cids)} tipos mais frequentes "
        f"({categoria.lower() if categoria == 'Todas as categorias' else categoria}). Cada linha soma 100%."
    )

    idades_cancer["CANCER"] = idades_cancer["DIAGNOSTICO_DETALHADO"] + " - " + idades_cancer["CID_NOME"]
    idades_cancer["CANCER"] = idades_cancer["CANCER"].apply(lambda nome: "<br>".join(textwrap.wrap(nome, 30)))

    # Casos de cada câncer em cada faixa etária (linhas = cânceres, colunas = faixas)
    casos_faixa = (
        idades_cancer.groupby(["CANCER", "FAIXA_ETARIA"], observed=False)
        .size()
        .unstack(fill_value=0)
    )
    casos_faixa.columns = casos_faixa.columns.astype(str)

    # Ordena pela idade mediana (mais jovem em cima)
    ordem = idades_cancer.groupby("CANCER")["IDADE_PACIENTE"].median().sort_values().index
    casos_faixa = casos_faixa.reindex(ordem)

    # Percentual de cada faixa dentro do câncer (cada linha soma 100%)
    perc_faixa = casos_faixa.div(casos_faixa.sum(axis=1), axis=0) * 100

    fig = px.imshow(
        perc_faixa,
        color_continuous_scale="Blues",
        aspect="auto",
        labels={"x": "Faixa etária (anos)", "y": "", "color": "% dos casos"},
    )
    fig.update_traces(
        customdata=casos_faixa.values,
        texttemplate="%{z:.1f}%",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Faixa etária: %{x} anos<br>"
            "Casos: %{customdata:,}<br>"
            "Percentual: %{z:.1f}% dos casos deste câncer"
            "<extra></extra>"
        ),
    )
    fig.update_xaxes(side="top")

    # Cada linha precisa caber o nome mais longo (nomes quebrados em várias linhas)
    linhas_nome = max((nome.count("<br>") + 1 for nome in perc_faixa.index), default=1)
    altura_linha = max(60, linhas_nome * 20)

    fig.update_layout(
        # Altura acompanha a quantidade de cânceres e o tamanho dos nomes
        height=max(300, len(perc_faixa) * altura_linha),
        margin=dict(t=10, b=10, l=10, r=10),
        separators=",.",
        hoverlabel=dict(bgcolor="white", font_color="#262730", font_size=13, align="left"),
    )
    st.plotly_chart(fig, use_container_width=True)