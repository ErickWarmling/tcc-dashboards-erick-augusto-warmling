# Dashboards para Análise de Dados Oncológicos do SUS em Santa Catarina

Repositório destinado ao desenvolvimento dos dashboards de oncologia do Sistema Único de Saúde (SUS) em Santa Catarina, como parte do Trabalho de Conclusão de Curso (TCC) do curso de Engenharia de Software da Universidade do Estado de Santa Catarina (UDESC).

---

## 📊 Módulos

| Módulo | Conteúdo |
| --- | --- |
| **Visão Geral** | Panorama dos casos: total de casos, evolução mensal dos diagnósticos, categorias de diagnóstico, cânceres mais frequentes e mapa dos casos por município de residência |
| **Perfil dos Casos** | Idade e sexo dos pacientes: pirâmide etária, distribuição das idades e cânceres mais frequentes por sexo e por faixa etária |
| **Diagnósticos** | Tipos de câncer por grupo da CID-10, estabelecimentos que mais diagnosticam e tempo até o início do tratamento, incluindo o prazo de 60 dias da Lei nº 12.732/12 |
| **Distribuição Geográfica** | Onde os pacientes moram e são tratados: tratamento fora do município de residência, distância até o tratamento, trajetos mais frequentes e principais polos de atendimento |

**Filtros:** período do diagnóstico, sexo, faixa etária e município de residência, aplicados a todos os módulos.

## 🛠️ Tecnologias

- Python
- Streamlit
- pandas
- Plotly
- PostgreSQL
- SQLAlchemy

## 🗂️ Dados

**Base principal:** banco PostgreSQL com 29.678 casos diagnosticados entre jan/2024 e abr/2026, os mesmos dados utilizados nos modelos preditivos do TCC.

**Arquivos auxiliares** (`data/auxiliares/`):

- `municipios_sc.csv`: API de Localidades do IBGE
- `mapa_sc.json`: API de Malhas Geográficas do IBGE
- `estabelecimentos.csv`: API de Dados Abertos do Ministério da Saúde (CNES)
- `CID-10-CATEGORIAS.CSV`: DATASUS

Os três primeiros são gerados pelos scripts da pasta `scripts/`:

```bash
python scripts/baixar_municipios.py
python scripts/baixar_mapa.py
python scripts/baixar_estabelecimentos.py   # requer o .env configurado
```

## 📁 Estrutura

```
dashboards/
├── app.py                  # Ponto de entrada (navegação e filtros)
├── db.py                   # Conexão com o banco e carga dos dados
├── pages/                  # Páginas do dashboard
├── scripts/                # Scripts de coleta dos dados auxiliares
├── data/auxiliares/        # Arquivos auxiliares
├── assets/                 # Imagens (logo)
├── .streamlit/config.toml  # Tema do Streamlit
├── requirements.txt        # Dependências
└── .env.example            # Modelo de conexão com o banco
```

## ▶️ Como executar

Dentro da pasta `dashboards/`:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Copie `.env.example` para `.env`, preencha os dados do banco e rode:

```bash
streamlit run app.py
```

---

## Autor

**Desenvolvido por:** [Erick Augusto Warmling](https://github.com/ErickWarmling)
