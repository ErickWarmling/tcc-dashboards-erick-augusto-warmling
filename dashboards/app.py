from pathlib import Path

import streamlit as st


st.set_page_config(page_title="Dashboards de Dados Oncológicos - SUS/SC", layout="wide")

# ==== Estilos (CSS) ====
# Vem antes de tudo: o Streamlit mostra o boneco de "Running..." 500 ms após iniciar,
# e o estilo que o esconde precisa chegar antes disso (o st.logo é lento na 1ª execução)
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
    /* Esconde o menu padrão do Streamlit (os três pontinhos no canto superior direito) */
    [data-testid="stMainMenu"] {
        display: none;
    }
    /* Esconde os botões que o Streamlit Cloud coloca no topo (compartilhar, GitHub, editar etc.),
       que ficariam por cima do período mostrado na navbar */
    [data-testid="stToolbarActions"],
    [data-testid="stAppDeployButton"] {
        display: none !important;
    }
    /* Esconde o aviso "Running..." do Streamlit: a tela de carregamento faz esse papel */
    [data-testid="stStatusWidget"] {
        display: none;
    }

    /* ---- Botões de fechar («) e abrir (») o menu lateral ---- */
    /* O de fechar fica sempre visível (por padrão só aparece ao passar o mouse) */
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        display: flex !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stExpandSidebarButton"] {
        width: 2.1rem;
        height: 2.1rem;
        color: #FFFFFF !important;
        background-color: rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 0.5rem;
        transition: background-color 0.2s;
    }
    [data-testid="stSidebarCollapseButton"] button:hover,
    [data-testid="stExpandSidebarButton"]:hover {
        background-color: rgba(255, 255, 255, 0.28) !important;
    }
    /* Ícone de três linhas (☰) no lugar das setas « e » */
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stExpandSidebarButton"] {
        display: flex !important;
        align-items: center;
        justify-content: center;
    }
    [data-testid="stSidebarCollapseButton"] button [data-testid="stIconMaterial"],
    [data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"] {
        display: none !important;
    }
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stExpandSidebarButton"] {
        position: relative;
    }
    /* As três linhas são desenhadas no centro exato do botão */
    [data-testid="stSidebarCollapseButton"] button::before,
    [data-testid="stExpandSidebarButton"]::before {
        content: "";
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        width: 1.1rem;
        height: 0.85rem;
        background:
            linear-gradient(#FFFFFF 0 0) top / 100% 2px no-repeat,
            linear-gradient(#FFFFFF 0 0) center / 100% 2px no-repeat,
            linear-gradient(#FFFFFF 0 0) bottom / 100% 2px no-repeat;
    }

    /* Menu fechado: esconde o logo do SUS que o Streamlit mostra no topo */
    [data-testid="stHeaderLogo"] {
        display: none !important;
    }

    /* Menu fechado: o botão de abrir fica no canto esquerdo do topo,
       então o título da navbar anda para a direita para não ficar embaixo dele */
    body:has([data-testid="stSidebar"][aria-expanded="false"]) .navbar {
        padding-left: 5.75rem;
    }

    /* ---- Área da página: navbar colada no topo ---- */
    [data-testid="stMainBlockContainer"] {
        padding: 0 2rem 2rem 2rem;
    }

    /* ---- Navbar fixa no topo ao rolar a página ---- */
    [data-testid="stElementContainer"]:has(.navbar) {
        position: sticky;
        top: 0;
        z-index: 990;
    }
    /* A barra de rolagem fica ao lado da navbar e deixa ver o fundo da área principal.
       Os 60px de cima desse fundo (a altura da navbar) são azuis, para o azul ir até a borda
       da tela. Como a navbar fica sempre no topo, os dois continuam emendados ao rolar. */
    [data-testid="stMain"] {
        background: linear-gradient(to bottom, #0B3B7B 0, #0B3B7B 3.75rem, #F5F7FB 3.75rem);
    }

    /* ---- Navbar ---- */
    .navbar {
        background-color: #0B3B7B;
        color: #FFFFFF;
        height: 3.75rem;
        margin: 0 -2rem 1.5rem -2rem;
        padding: 0 2rem 0 2rem;
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

    /* ---- Cards: ícone discreto ao lado do título ---- */
    /* A linha do título tem a mesma altura do círculo: texto e círculo ficam centralizados juntos */
    [data-testid="stMetricLabel"] p:has(> span:first-child),
    [data-testid="stMetricLabel"] div:has(> [data-testid="stMarkdownContainer"] p > span:first-child),
    [data-testid="stMetricLabel"] [data-testid="stMarkdownContainer"]:has(p > span:first-child) {
        line-height: 1.75rem;
    }
    /* O ícone (:material/...:) vira um <span> no início do título do card */
    [data-testid="stMetric"] [data-testid="stMetricLabel"] p > span:first-child {
        /* O Streamlit põe display e vertical-align direto no elemento: o !important vence esse estilo */
        display: inline-flex !important;
        vertical-align: top !important;
        align-items: center;
        justify-content: center;
        width: 1.75rem;
        height: 1.75rem;
        margin-right: 0.45rem;
        line-height: 1;
        /* a fonte de ícones desenha o glifo um pouco acima do meio: o recuo de cima o desce */
        box-sizing: border-box;
        padding-top: 0.25rem;
        font-size: 1.1rem !important;
        color: #1B59B7;
        background-color: #E8EEF9;
        border-radius: 50%;
    }

    /* ---- Tela de carregamento dos dados ---- */
    /* Só aparece após 0.15s: com os dados já em cache ela some antes disso e não pisca */
    .carregando {
        position: fixed;
        inset: 0;
        z-index: 999999;
        background-color: #F5F7FB;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        opacity: 0;
        animation: carregando-aparecer 0.2s ease-out 0.15s forwards;
    }
    .carregando-icone {
        width: 3rem;
        height: 3rem;
        margin-bottom: 0.75rem;
        border: 0.3rem solid #E8EEF9;
        border-top-color: #1B59B7;
        border-radius: 50%;
        animation: carregando-girar 0.9s linear infinite;
    }
    .carregando-titulo {
        color: #0B3B7B;
        font-size: 1.15rem;
        font-weight: 600;
    }
    .carregando-texto {
        color: #6B7280;
        font-size: 0.9rem;
    }
    @keyframes carregando-aparecer {
        to { opacity: 1; }
    }
    @keyframes carregando-girar {
        to { transform: rotate(360deg); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==== Logo no topo do menu lateral ====
# Caminho a partir da pasta deste arquivo: funciona mesmo se o app for iniciado de outra pasta
st.logo(Path(__file__).parent / "assets" / "logo_sus.png", size="large")

# ==== Menu lateral (páginas) ====
pg = st.navigation([
    st.Page("pages/visao_geral.py", title="Visão Geral", icon=":material/dashboard:", default=True),
    st.Page("pages/perfil_casos.py", title="Perfil dos Casos", icon=":material/groups:"),
    st.Page("pages/diagnosticos.py", title="Diagnósticos", icon=":material/stethoscope:"),
    st.Page("pages/distribuicao_geografica.py", title="Distribuição Geográfica", icon=":material/map:"),
])

# ==== Tela de carregamento (enquanto os dados não estão em cache) ====
tela_carregamento = st.empty()
tela_carregamento.markdown(
    """
    <div class="carregando" role="status">
        <div class="carregando-icone"></div>
        <span class="carregando-titulo">Carregando os dados oncológicos</span>
        <span class="carregando-texto">Os dados estão sendo carregados, aguarde um instante.</span>
    </div>
    """,
    unsafe_allow_html=True,
)
try:
    # Importado aqui porque o db.py é lento para abrir (pandas, sqlalchemy):
    # assim a tela já aparece enquanto ele carrega
    from db import OUTROS_ESTADOS, carregar_dados, nome_mes

    carregar_dados()
finally:
    # Tira a tela mesmo em caso de erro, para a mensagem do erro ficar visível
    tela_carregamento.empty()

# ==== Filtros (menu lateral, abaixo das abas) ====
meses_disponiveis = sorted(carregar_dados()["ANO_MES_DIAGNOSTICO"].unique())


# Valores iniciais dos filtros (usados ao abrir o dashboard e no botão "Limpar filtros")
FILTROS_INICIAIS = {
    "filtro_inicio": meses_disponiveis[0],
    "filtro_fim": meses_disponiveis[-1],
    "filtro_periodo": (meses_disponiveis[0], meses_disponiveis[-1]),
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


def aplicar_periodo():
    """Guarda o período escolhido para a dados_filtrados() (db.py)."""
    st.session_state["filtro_periodo"] = (
        st.session_state["filtro_inicio"],
        st.session_state["filtro_fim"],
    )


@st.fragment
def selecionar_periodo():
    """Campos De/Até: cada um só oferece meses compatíveis com o outro."""
    st.markdown("**Período do diagnóstico**")
    col_de, col_ate = st.columns(2)

    # Os valores iniciais vêm de FILTROS_INICIAIS (por isso não há index/default nos campos)
    col_de.selectbox(
        "De",
        options=[mes for mes in meses_disponiveis if mes <= st.session_state["filtro_fim"]],
        format_func=nome_mes,
        key="filtro_inicio",
    )
    col_ate.selectbox(
        "Até",
        options=[mes for mes in meses_disponiveis if mes >= st.session_state["filtro_inicio"]],
        format_func=nome_mes,
        key="filtro_fim",
    )


# Município de residência (código -> nome, em ordem alfabética)
dados_completos = carregar_dados()
nomes_residencia = (
    dados_completos.dropna(subset=["MUNICIPIO_RESIDENCIA_NOME"])
    .drop_duplicates("MUNICIPIO_RESIDENCIA")
    .set_index("MUNICIPIO_RESIDENCIA")["MUNICIPIO_RESIDENCIA_NOME"]
    .sort_values()
)

with st.sidebar:
    st.header("Filtros")

    # Fora do formulário: dentro dele, um campo não reage ao outro até clicar no botão
    selecionar_periodo()

    # Formulário: as escolhas só são aplicadas ao clicar em "Aplicar filtros"
    with st.form("form_filtros", border=False):
        # ---- Sexo ----
        st.segmented_control(
            "Sexo",
            options=["Todos", "Feminino", "Masculino"],
            key="filtro_sexo",
        )

        # ---- Faixa etária ----
        st.multiselect(
            "Faixa etária",
            options=list(dados_completos["FAIXA_ETARIA"].cat.categories),
            placeholder="Todas",
            key="filtro_faixa_etaria",
        )

        # ---- Município de residência ----
        st.multiselect(
            "Município de residência",
            options=[*nomes_residencia.index, OUTROS_ESTADOS],
            format_func=lambda codigo: nomes_residencia.get(codigo, codigo),
            placeholder="Todos",
            key="filtro_municipio",
        )

        # ---- Botões ----
        st.form_submit_button(
            "Aplicar filtros",
            on_click=aplicar_periodo,
            type="primary",
            icon=":material/filter_alt:",
            width="stretch",
        )
        st.form_submit_button(
            "Limpar filtros", on_click=limpar_filtros, icon=":material/restart_alt:", width="stretch"
        )

# ==== Navbar ====
inicio, fim = st.session_state["filtro_periodo"]

ICONE_CALENDARIO = """
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
  <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/>
  <line x1="8" y1="2" x2="8" y2="6"/><line x1="16" y1="2" x2="16" y2="6"/>
</svg>"""

st.markdown(
    f"""
    <div class="navbar">
        <span class="navbar-titulo">Dashboard de Dados Oncológicos – SUS/SC</span>
        <div class="navbar-direita">
            <span class="navbar-item">{ICONE_CALENDARIO} Período: {nome_mes(inicio)} a {nome_mes(fim)}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

pg.run()