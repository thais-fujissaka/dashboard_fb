import streamlit as st
import pandas as pd
import pymysql
from utils.functions.general_functions import config_sidebar
from utils.queries_conciliacao import GET_CASAS
from utils.components import button_download, seletor_ano

pd.set_option('future.no_silent_downcasting', True)


st.set_page_config(
    page_title="Análises e Objetivos",
    page_icon=":material/assignment:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title(":material/assignment: Análises e Objetivos")
st.divider()

# Seletor de casa e ano
col1, col2 = st.columns(2)

with col1:
    df_casas = GET_CASAS()
    casas = df_casas['Casa'].tolist()
    casa = st.selectbox("Selecione a casa referente ao arquivo de Orçamentos:", casas)

    # Recupera id da casa
    mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))
    id_casa = mapeamento_casas[casa]
    
with col2:
    ano = seletor_ano(2025, 2026, 'ano', 'Selecione o ano refente ao orçamento:')

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(['Análise SWOT', 'Análise Interna', 'Exemplo de Rotinas Gerais', f'Proposta de Objetivos {ano}', 'Planejamento de Marketing'])
with tab1:
    # CSS na Análise SWOT
    st.markdown("""
        <style>
        .swot-box {
            border: 1px solid #000;
            padding: 16px;
            height: 25em;
        }
        .swot-title {
            font-weight: 700;
            text-align: center;
            padding: 6px;
            margin: -16px -16px 12px -16px;
            color: white;
        }
        .forcas { background-color: #8BC34A; }
        .fraquezas { background-color: #FF9800; }
        .oportunidades { background-color: #0070C0; }
        .ameacas { background-color: #F44336; color: white; }

        .swot-list li {
            margin-bottom: 6px;
        }
        </style>
        """, unsafe_allow_html=True
    )

    st.subheader("Análise SWOT")
    st.divider()

    col_esq, col_dir = st.columns(2)

    # --------- FORÇAS ---------
    with col_esq:
        st.markdown("""
        <h6 style="text-align: center;">FATORES INTERNOS</h6>
        <div class="swot-box">
            <div class="swot-title forcas">FORÇAS</div>
            <ul class="swot-list">
                <li>Marca icônica e legado histórico — Um dos bares mais tradicionais e reconhecidos de São Paulo, símbolo da boemia paulistana.</li>
                <li>Localização estratégica — Esquina da Av. Ipiranga com Av. São João, ponto turístico e de alto fluxo.</li>
                <li>Ambiente histórico preservado — Fachada tombada, interior clássico, atmosfera autêntica e nostálgica.</li>
                <li>Programação musical de qualidade — Atrações diárias de samba, MPB e choro, fortalecendo o vínculo cultural.</li>
                <li>Alta lembrança de marca — Forte presença em mídia, guias turísticos e plataformas de avaliação.</li>
                <li>Mix gastronômico completo — Combina bar, restaurante e casa de shows em um só lugar, ampliando o público-alvo.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # --------- OPORTUNIDADES ---------
    with col_dir:
        st.markdown("""
        <h6 style="text-align: center;">FATORES EXTERNOS</h6>
        <div class="swot-box">
            <div class="swot-title oportunidades">OPORTUNIDADES</div>
            <ul class="swot-list">
                <li>Turismo cultural e gastronômico em alta — Crescimento do fluxo de visitantes no Centro Histórico e roteiros.</li>
                <li>Parcerias institucionais — Possibilidade de eventos com Secretaria de Cultura, SPTuris entre outros.</li>
                <li>Expansão digital e delivery  — Uso da marca para vender produtos que vão desde AeB à Lojinha</li>
                <li>Reposicionamento para público jovem — Criação de experiências que possam combinar gastronomia + cultura + conteúdo digital.</li>
                <li>Requalificação do Centro — Programas públicos e privados de revitalização urbana elevam segurança e valorizam imóveis.</li>
                <li>Exploração de storytelling e branding — A história de 70 anos é um ativo que pode ser ainda mais explorado e que pode gerar grandes campanhas.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    col_esq2, col_dir2 = st.columns(2, vertical_alignment='center')

    # --------- FRAQUEZAS ---------
    with col_esq2:
        st.markdown("""
        <div class="swot-box"">
            <div class="swot-title fraquezas">FRAQUEZAS</div>
            <ul class="swot-list">
                <li>Custo operacional elevado — Estrutura grande, som ao vivo e equipe numerosa.</li>
                <li>Desgaste da imagem no público local — Parte dos paulistanos associa o Brahma mais a “atração turística” do que a ponto de encontro cotidiano.</li>
                <li>Dependência de eventos e shows — A operação noturna e musical concentra grande parte da receita, gerando sazonalidade.</li>
                <li>Atendimento irregular — Relatos de inconsistência na hospitalidade e tempo de espera em plataformas de avaliação/ Cliente Oculto</li>
                <li>Dificuldade de acesso e estacionamento — Zona central com problemas de mobilidade e segurança no entorno.</li>
                <li>Gestão de experiência heterogênea — Diferença percebida entre dias de semana (fluxo menor) e noites de evento (lotação máxima).</li>
            </ul>
        </div>
        <h6 style="text-align: center; margin-top: 15px;">FATORES INTERNOS</h6>
        """, unsafe_allow_html=True)

    # --------- AMEAÇAS ---------
    with col_dir2:
        st.markdown("""
        <div class="swot-box">
            <div class="swot-title ameacas">AMEAÇAS</div>
            <ul class="swot-list">
                <li>Concorrência crescente — Novos bares e rooftops em regiões revitalizadas (Centro Novo, Pinheiros, Vila Madalena) podem atrair o mesmo público.</li>
                <li>Oscilação de fluxo no entorno — Questões de segurança, limpeza urbana e transporte afetam frequência noturna.</li>
                <li>Mudanças no perfil de consumo — Jovens priorizando experiências mais casuais, menos formais e de ticket médio menor.</li>
                <li>Inflação e custos de insumos — Preço de bebidas e alimentos afetando margens e percepção de valor.</li>
                <li>Dependência da imagem histórica — O excesso de apego ao passado pode dificultar inovações no cardápio e no ambiente.</li>
            </ul>
        </div>
        <h6 style="text-align: center; margin-top: 15px;">FATORES EXTERNOS</h6>
        """, unsafe_allow_html=True)

    st.divider()

    # Legenda
    st.markdown(f"""
        <div style="display: flex; flex-direction: column; gap:1em; padding:10px; border:1px solid #ccc; border-radius:8px";>
            <span style="font-size: 16px"><b>Interno:</b> diz respeito ao que está dentro da empresa — aquilo que ela <b>controla</b> (pessoas, processos, estrutura, marca, finanças).</span>
            <span style="font-size: 16px"><b>Externo: </b> são fatores fora do controle direto — o <b>mercado, concorrência, economia, comportamento do consumidor</b>, etc.</span>
        </div>
        """, unsafe_allow_html=True)
    

with tab4:
    # CSS do Planejamento de Objetivos
    st.markdown("""
        <style>
        .card {
            border: 1px solid #000;
            # background-color: #FFFDE7;
        }

        .card-title {
            font-weight: 700;
            text-align: center;
            padding: 8px;
            # margin: -16px -16px 12px -16px;
            color: white;
        }

        .title-blue { background-color: #4F79C7; }
        .title-green { background-color: #7CB342; }
        .title-orange { background-color: #F28C38; }

        .kpi-item {
            border-top: 1px solid #000;
            padding: 8px;
            text-align: center;
        }

        .table-header {
            display: grid;
            grid-template-columns: 40% 60%;
            font-weight: 700;
            color: white;
            background-color: #F28C38;
            padding: 8px;
        }

        .table-row {
            display: grid;
            grid-template-columns: 40% 60%;
            border-top: 1px solid #000;
            padding: 8px;
            # background-color: #FFFDE7;
        }

        .table-row b {
            font-weight: 700;
        }
        </style>
        """, unsafe_allow_html=True
    )

    st.subheader(f"Proposta de Objetivos {ano}")
    st.divider()

    col_esq, col_dir = st.columns([1, 1.4], vertical_alignment='center')

    # -------- COLUNA ESQUERDA --------
    with col_esq:
        # OBJETIVO GERAL
        st.markdown(f"""
        <div class="card">
            <div class="card-title title-blue">OBJETIVO GERAL {ano}</div>
            <p style="padding: 12px 16px 0 16px; text-align: center">
                Reforçar o posicionamento como símbolo cultural e gastronômico do centro,
                expandir o público-alvo e rejuvenescimento de marca, além de nos consolidar
                como bar de recorrência apesar do turismo.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.write("")

        # KPIs
        st.markdown("""
        <div class="card">
            <div class="card-title title-green">KPIs para Análise de Desempenho</div>
            <div class="kpi-item">NPS</div>
            <div class="kpi-item">CMV</div>
            <div class="kpi-item">Rentabilidade Artística</div>
        </div>
        """, unsafe_allow_html=True)

    # -------- COLUNA DIREITA --------
    with col_dir:
        st.markdown("""
        <div class="card" style="padding:0">
            <div class="table-header">
                <div>PRINCIPAIS RESPONSABILIDADES</div>
                <div>DESCRIÇÃO</div>
            </div>
            <div class="table-row">
                <div><b>Melhorar percepção de serviço</b></div>
                <div>
                    Implantar programa de treinamento contínuo de hospitalidade baseado em
                    padrões de casas premium (experiência de mesa, apresentação e tempo de resposta)
                </div>
            </div>
            <div class="table-row">
                <div><b>Melhorar percepção de serviço</b></div>
                <div>
                    Revisar layout operacional e rotas de garçons, otimizando fluxo
                </div>
            </div>
            <div class="table-row">
                <div><b>Incrementar receitas por meio de novos canais e produtos</b></div>
                <div>
                    Lançar linha de produtos Brahma
                </div>
            </div>
            <div class="table-row">
                <div><b>Controle de CMV</b></div>
                <div>
                    Mapear custos de produção e CMV com dashboards mensais e metas por categoria
                </div>
            </div>
            <div class="table-row">
                <div><b>NPS</b></div>
                <div>
                    Melhorar Nota Google e outras plataformas
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
