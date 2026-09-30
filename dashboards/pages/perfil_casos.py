import textwrap
import plotly.express as px
import streamlit as st
from db import carregar_dados

df = carregar_dados()

# ==== Título ====
st.title("👥 Perfil dos Casos")
st.caption("Idade e sexo dos casos oncológicos diagnosticados e tratados em Santa Catarina (jan/2024 a abr/2024)")

# ==== Cálculo dos cards ====
idade_media = df["IDADE_PACIENTE"].mean()
perc_masculino = (df["SEXO_PACIENTE"] == "M").mean() * 100
perc_feminino = (df["SEXO_PACIENTE"] == "F").mean() * 100
faixa_predominante = df["FAIXA_ETARIA"].value_counts().idxmax()

# ==== Cards ====
col1, col2, col3, col4 = st.columns(4)

col1.metric("Idade média", f"{idade_media:.1f} anos".replace(".", ","), border=True)
col2.metric("Masculino", f"{perc_masculino:.1f}%".replace(".", ","), border=True)
col3.metric("Feminino", f"{perc_feminino:.1f}%".replace(".", ","), border=True)
col4.metric("Faixa etária predominante", f"{faixa_predominante} anos", border=True)

# ==== Linha 1 de gráficos ====
graf_esq, graf_dir = st.columns(2)

# ==== Pirâmide etária ====
with graf_esq.container(border=True):
    st.subheader("Pirâmide etária")

    piramide = (
        df.groupby(["FAIXA_ETARIA", "SEXO_NOME"], observed=False)
        .size()
        .reset_index(name="CASOS")
    )

    # Homens ficam com valor negativo para as barras irem para a esquerda
    piramide["CASOS_GRAFICO"] = piramide["CASOS"].where(
        piramide["SEXO_NOME"] == "Feminino", -piramide["CASOS"]
    )

    fig = px.bar(
        piramide,
        x="CASOS_GRAFICO",
        y="FAIXA_ETARIA",
        color="SEXO_NOME",
        orientation="h",
        custom_data=["CASOS"],
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
        hovertemplate="<b>%{fullData.name}</b><br>Faixa: %{y}<br>Casos: %{customdata[0]}<extra></extra>"
    )
    fig.update_layout(
        barmode="relative",
        bargap=0.1,
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(t=30, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Distribuição dos casos por sexo ====
with graf_dir.container(border=True):
    st.subheader("Distribuição dos casos por sexo")

    casos_sexo = (
        df.groupby("SEXO_NOME")
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
        color_discrete_map={"Masculino": "#1B59B7", "Feminino": "#E26D9A"},
        labels={"SEXO_NOME": "", "CASOS": "Casos"},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_yaxes(range=[0, casos_sexo["CASOS"].max() * 1.15])
    fig.update_layout(
        showlegend=False,
        bargap=0.5,
        height=450,
        margin=dict(t=30, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Linha 2 de gráficos ====
graf2_esq, graf2_dir = st.columns(2)

# ==== Distribuição da idade ====
with graf2_esq.container(border=True):
    st.subheader("Distribuição da idade")

    fig = px.histogram(
        df,
        x="IDADE_PACIENTE",
        color_discrete_sequence=["#1B59B7"],
        labels={"IDADE_PACIENTE": "Idade no diagnóstico (anos)"},
    )

    # Linha tracejada na idade média
    fig.add_vline(
        x=idade_media,
        line_dash="dash",
        line_color="#F28C28",
        annotation_text=f"Média: {idade_media:.1f} anos".replace(".", ","),
        annotation_position="top left",
    )

    fig.update_layout(
        yaxis_title="Casos",
        bargap=0.05,
        height=450,
        margin=dict(t=30, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)

# ==== Faixa etária × categoria do diagnóstico ====
with graf2_dir.container(border=True):
    st.subheader("Faixa etária × categoria do diagnóstico")

    faixa_categoria = (
        df.groupby(["FAIXA_ETARIA", "CATEGORIA_NOME"], observed=False)
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
        hovertemplate="<b>%{fullData.name}</b><br>Faixa: %{x}<br>%{y:.1f}% (%{customdata[0]} casos)<extra></extra>"
    )
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    fig.update_layout(
        barmode="stack",
        bargap=0.2,
        height=450,
        legend=dict(orientation="v", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=30, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)


# ==== Principais tipos de câncer por sexo ====
def grafico_principais_canceres(dados, cor):
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

    fig = px.bar(
        top_cids,
        x="CASOS",
        y="CANCER",
        orientation="h",
        text="CASOS",
        color_discrete_sequence=[cor],
        labels={"CASOS": "Casos", "CANCER": ""},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(range=[0, top_cids["CASOS"].max() * 1.15])
    fig.update_layout(height=550, bargap=0.4, margin=dict(t=10, b=10, l=10, r=10))
    return fig


with st.container(border=True):
    st.subheader("Principais tipos de câncer por sexo")

    col_masc, col_fem = st.columns(2)

    with col_masc:
        st.markdown("**Masculino**")
        casos_masc = df[df["SEXO_PACIENTE"] == "M"]
        st.plotly_chart(grafico_principais_canceres(casos_masc, "#1B59B7"), use_container_width=True)

    with col_fem:
        st.markdown("**Feminino**")
        casos_fem = df[df["SEXO_PACIENTE"] == "F"]
        st.plotly_chart(grafico_principais_canceres(casos_fem, "#E26D9A"), use_container_width=True)


# ==== Idade × tipo de câncer ====
with st.container(border=True):
    st.subheader("Idade × tipo de câncer")
    st.caption("Distribuição das idades nos 10 tipos de câncer mais frequentes")

    # Os 10 cânceres mais frequentes
    top10_cids = df["DIAGNOSTICO_DETALHADO"].value_counts().nlargest(10).index
    idades_cancer = df[df["DIAGNOSTICO_DETALHADO"].isin(top10_cids)].copy()

    idades_cancer["CANCER"] = idades_cancer["DIAGNOSTICO_DETALHADO"] + " - " + idades_cancer["CID_NOME"]
    idades_cancer["CANCER"] = idades_cancer["CANCER"].apply(lambda nome: "<br>".join(textwrap.wrap(nome, 30)))

    # Ordena pela idade mediana (mais jovem embaixo, mais velho em cima)
    ordem = idades_cancer.groupby("CANCER")["IDADE_PACIENTE"].median().sort_values().index.tolist()

    fig = px.box(
        idades_cancer,
        x="IDADE_PACIENTE",
        y="CANCER",
        orientation="h",
        category_orders={"CANCER": ordem[::-1]},
        color_discrete_sequence=["#1B59B7"],
        labels={"IDADE_PACIENTE": "Idade no diagnóstico (anos)", "CANCER": ""},
    )
    fig.update_layout(height=650, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)