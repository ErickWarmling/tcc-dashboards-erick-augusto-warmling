import streamlit as st

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
    st.Page("pages/estabelecimentos.py", title="Estabelecimentos", icon="🏥"),
    st.Page("pages/distribuicao_temporal.py", title="Distribuição Temporal", icon="📅"),
])

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
            <span class="navbar-item">{ICONE_CALENDARIO} Período: jan/2024 a abr/2026</span>
            <span class="navbar-info" title="Fonte: Painel-Oncologia (DATASUS). Casos diagnosticados e tratados em SC.">{ICONE_INFO}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

pg.run()