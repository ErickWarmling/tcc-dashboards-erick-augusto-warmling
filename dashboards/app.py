import streamlit as st
from db import carregar_dados, nome_mes


st.set_page_config(page_title="Dashboards de Dados Oncológicos - SUS/SC", layout="wide")

# ==== Logo no topo do menu lateral ====
st.logo("assets/logo_sus.png", size="large")

# ==== Estilos (CSS) ====
st.markdown(
    """
    <style>
    /* ---- Esconde o espaço ocupado por este bloco de estilos ---- */
    [data-testid="stElementContainer"]:has(style) {
        display: none;
    }

    /* ---- Logo ---- */
    [data-testid="stSidebarHeader"] {
        padding-left: 1rem;
    }
    [data-testid="stSidebarLogo"] {
        height: 4.5rem;
        max-width: 100%;
        object-fit: contain;
        object-position: left;
    }

    /* ---- Aba selecionada no menu ---- */
    [data-testid="stSidebarNavLink"][aria-current="page"] {
        background-color: #1B59B7;
    }

    /* ---- Cabeçalho padrão do Streamlit: transparente, por cima da navbar ---- */
    [data-testid="stHeader"] {
        background: transparent;
    }
    [data-testid="stHeader"] button {
        color: #FFFFFF;
    }

    /* ---- Área da página: navbar colada no topo ---- */
    [data-testid="stMainBlockContainer"] {
        padding: 0 2rem 2rem 2rem;
    }

    /* ---- Navbar ---- */
    .navbar {
        background-color: #0B3B7B;
        color: #FFFFFF;
        height: 3.75rem;
        margin: 0 -2rem 1.5rem -2rem;
        padding: 0 4rem 0 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .navbar-titulo {
        font-size: 1.4rem;
        font-weight: 600;
    }
    .navbar-direita {
        display: flex;
        align-items: center;
        gap: 1.25rem;
        font-size: 0.9rem;
    }
    .navbar-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .navbar-info {
        cursor: help;
        display: flex;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==== Menu lateral (páginas) ====
pg = st.navigation([
    st.Page("pages/visao_geral.py", title="Visão Geral", icon="📊", default=True),
    st.Page("pages/perfil_casos.py", title="Perfil dos Casos", icon="👥"),
    st.Page("pages/diagnosticos.py", title="Diagnósticos", icon="🩺"),
    st.Page("pages/distribuicao_geografica.py", title="Distribuição Geográfica", icon="🗺️"),
])

# ==== Filtros (menu lateral, abaixo das abas) ====
meses_disponiveis = sorted(carregar_dados()["ANO_MES_DIAGNOSTICO"].unique())


# Valores iniciais dos filtros (usados ao abrir o dashboard e no botão "Limpar filtros")
FILTROS_INICIAIS = {
    "filtro_inicio": meses_disponiveis[0],
    "filtro_fim": meses_disponiveis[-1],
    "filtro_sexo": "Todos",
    "filtro_faixa_etaria": [],
    "filtro_municipio": [],
}

for chave, valor in FILTROS_INICIAIS.items():
    if chave not in st.session_state:
        st.session_state[chave] = list(valor) if isinstance(valor, list) else valor


def limpar_filtros():
    """Volta todos os filtros do menu lateral ao estado inicial."""
    for chave, valor in FILTROS_INICIAIS.items():
        st.session_state[chave] = list(valor) if isinstance(valor, list) else valor


with st.sidebar:
    st.header("Filtros")

    st.markdown("**Período do diagnóstico**")
    col_de, col_ate = st.columns(2)

    # Os valores iniciais vêm de FILTROS_INICIAIS (por isso não há index/default nos campos)
    inicio = col_de.selectbox(
        "De",
        options=meses_disponiveis,
        format_func=nome_mes,
        key="filtro_inicio",
    )
    fim = col_ate.selectbox(
        "Até",
        options=meses_disponiveis,
        format_func=nome_mes,
        key="filtro_fim",
    )

    # Se o início vier depois do fim, inverte os dois
    if inicio > fim:
        inicio, fim = fim, inicio

    # Guarda o período para a dados_filtrados() (db.py)
    st.session_state["filtro_periodo"] = (inicio, fim)

    # ---- Sexo ----
    st.segmented_control(
        "Sexo",
        options=["Todos", "Feminino", "Masculino"],
        key="filtro_sexo",
    )

    # ---- Faixa etária ----
    st.multiselect(
        "Faixa etária",
        options=list(carregar_dados()["FAIXA_ETARIA"].cat.categories),
        placeholder="Todas",
        key="filtro_faixa_etaria",
    )

    # ---- Município de residência (código -> nome, em ordem alfabética) ----
    dados_completos = carregar_dados()
    nomes_residencia = (
        dados_completos.dropna(subset=["MUNICIPIO_RESIDENCIA_NOME"])
        .drop_duplicates("MUNICIPIO_RESIDENCIA")
        .set_index("MUNICIPIO_RESIDENCIA")["MUNICIPIO_RESIDENCIA_NOME"]
        .sort_values()
    )
    st.multiselect(
        "Município de residência",
        options=nomes_residencia.index.tolist(),
        format_func=lambda codigo: nomes_residencia[codigo],
        placeholder="Todos",
        key="filtro_municipio",
    )

    st.button("Limpar filtros", on_click=limpar_filtros, width="stretch")

# ==== Navbar ====
ICONE_CALENDARIO = """
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
  <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/>
  <line x1="8" y1="2" x2="8" y2="6"/><line x1="16" y1="2" x2="16" y2="6"/>
</svg>"""

ICONE_INFO = """
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
  <circle cx="12" cy="12" r="10"/><line x1="12" y1="11" x2="12" y2="17"/>
  <circle cx="12" cy="7.5" r="0.5" fill="white"/>
</svg>"""

st.markdown(
    f"""
    <div class="navbar">
        <span class="navbar-titulo">Dashboard de Dados Oncológicos – SUS/SC</span>
        <div class="navbar-direita">
            <span class="navbar-item">{ICONE_CALENDARIO} Período: {nome_mes(inicio)} a {nome_mes(fim)}</span>
            <span class="navbar-info" title="Fonte: Painel-Oncologia (DATASUS). Casos diagnosticados e tratados em SC.">{ICONE_INFO}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

pg.run()