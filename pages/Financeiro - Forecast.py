import streamlit as st
# from utils.functions.cmv import config_faturamento_eventos
from utils.functions.forecast import *
from utils.functions.general_functions import config_sidebar
from utils.functions.general_functions_conciliacao import *
from utils.queries_conciliacao import GET_CASAS
from utils.queries_forecast import *


st.set_page_config(
    page_title="Forecast",
    page_icon=":material/event_upcoming:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

col1, col2 = st.columns([5, 1], vertical_alignment='center')
with col1:
    st.title(":material/event_upcoming: Forecast")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()


# Dados - Faturamento Diário
df_casas = GET_CASAS()
(df_faturamento_agregado_dia, 
 df_faturamento_eventos, 
 df_parc_receitas_extr, 
 df_parc_receit_extr_dia) = GET_TODOS_FATURAMENTOS_DIA()

# Filtrando Datas
datas = calcular_datas()

# Seletor de casa
casas = df_casas['Casa'].tolist()

# Troca o valor na lista
casas = [c for c in casas if c != 'All bar']
casa = st.selectbox("Selecione uma casa:", casas)
st.divider()

# Definindo um dicionário para mapear nomes de casas a IDs de casas
mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))

# Obtendo o ID da casa selecionada
id_casa = mapeamento_casas[casa]

tab1, tab2, tab3 = st.tabs(['Projeções - Mês corrente', 'Projeções - Próximos meses', 'Custos Artístico Geral'])


###################### PROJEÇÃO DE FATURAMENTO - MÊS CORRENTE ###################### 
with tab1:
    st.markdown(f'''
        <h3>Projeções - {casa} - {datas['amanha'].strftime('%d/%m/%Y')} a {datas['fim_mes_atual'].strftime('%d/%m/%Y')}</h3>
        ''', unsafe_allow_html=True)
    st.divider()

    # Prepara df de faturamento agregado diário para a casa selecionada
    df_faturamento_agregado_mes_corrente = prepara_dados_faturam_agregado_diario(id_casa, df_faturamento_agregado_dia, datas['inicio_mes_anterior'], datas['fim_mes_atual'])

    # --- CRIA COMBINAÇÃO DE TODAS AS CATEGORIAS x DIAS (mês anterior e corrente) ---
    df_dias_futuros_com_categorias = lista_dias_mes_anterior_atual(datas['ano_atual'], datas['mes_atual'], datas['ultimo_dia_mes_atual'], 
    datas['ano_anterior'], datas['mes_anterior'],
    df_faturamento_agregado_mes_corrente)

    # Gera projeção para prox dias do mês corrente por dia da semana
    df_dias_futuros_mes = cria_projecao_mes_corrente(df_faturamento_agregado_mes_corrente, df_dias_futuros_com_categorias, datas['today'])

    # Container que exibe projeção dos prox dias do mês corrente
    with st.container(border=True):
        st.markdown(f'''
            <h4>Faturamentos por categoria</h4>
            <p><strong>Premissa</strong> (para todas as categorias de faturamento, exceto 'Eventos' e 'Outras Receitas'): por dia da semana, é calculada a média de faturamento baseada nas das duas últimas semanas.</p>
            ''', unsafe_allow_html=True)

        exibe_faturamento_categoria('A&B', df_dias_futuros_mes, datas['today'])
        exibe_faturamento_categoria('Gifts', df_dias_futuros_mes, datas['today'])
        exibe_faturamento_categoria('Delivery', df_dias_futuros_mes, datas['today'])
        exibe_faturamento_categoria('Couvert', df_dias_futuros_mes, datas['today'])
        exibe_faturamento_eventos(df_faturamento_eventos, id_casa, datas)
        exibe_faturamento_outras_receitas(df_parc_receit_extr_dia, df_parc_receitas_extr, id_casa, datas)

    st.divider()
        
    # Container que exibe faturamento real e projetado dos dias anteriores do mês corrente
    with st.container(border=True):
        exibe_faturamento_dias_anteriores(df_dias_futuros_mes, datas)


###################### PROJEÇÃO DE FATURAMENTO - PRÓXIMOS MESES ###################### 
with tab2:
    # Dados - Faturamento e Orçamento Mensal
    df_orcamentos = GET_ORCAMENTOS()
    df_faturamento_zig_mensal, df_faturamento_agregado_mes = GET_TODOS_FATURAMENTOS_MENSAL(df_faturamento_agregado_dia, df_faturamento_eventos, df_parc_receit_extr_dia)
    
    st.markdown(f'''
        <h3>Projeções - {casa} - Próximos meses</h3>
        ''', unsafe_allow_html=True)
    st.divider()

    # Prepara df de faturamento agregado mensal para a casa selecionada
    df_faturamento_mes_casa, df_faturamento_orcamento = prepara_dados_faturamento_orcamentos_mensais(id_casa, df_orcamentos, df_faturamento_agregado_mes, datas['ano_passado'], datas['ano_atual'])

    # --- CRIA COMBINAÇÃO DE TODAS AS CATEGORIAS x MESES (ano corrente) ---
    df_meses_futuros_com_categorias = lista_meses_ano(df_faturamento_mes_casa, datas['ano_atual'], datas['ano_passado'])

    # Gera projeção para prox meses do ano
    df_faturamento_meses_futuros = projecao_faturamento_meses_seguintes(df_faturamento_orcamento, df_meses_futuros_com_categorias, datas['ano_atual'], datas['mes_atual'])

    # Container que exibe projeção dos prox meses
    with st.container(border=True):
        st.markdown(f'''
            <h4>Faturamentos por categoria</h4>
            <p><strong>Premissa</strong> (para todas as categorias de faturamento): média do percentual (%) de atingimento do Faturamento Real dos últimos dois meses x Orçamento.</p>
            ''', unsafe_allow_html=True)

        exibe_categoria_faturamento_prox_meses('A&B', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
        exibe_categoria_faturamento_prox_meses('Gifts', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
        exibe_categoria_faturamento_prox_meses('Delivery', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
        exibe_categoria_faturamento_prox_meses('Couvert', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
        exibe_categoria_faturamento_prox_meses('Eventos', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
        exibe_categoria_faturamento_prox_meses('Outras Receitas', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])

    st.divider()

    # Projeção de CMV 
    df_faturamento_zig, faturamento_bruto_alimentos, faturamento_bruto_bebidas, faturamento_delivery = config_faturamento_bruto_zig(df_faturamento_agregado_dia, datas['jan_ano_atual'], datas['dez_ano_atual'], casa)
    df_faturamento_eventos = config_faturamento_eventos(datas['jan_ano_atual'], datas['dez_ano_atual'], casa, faturamento_bruto_alimentos, faturamento_bruto_bebidas)
    df_compras, compras_alimentos, compras_bebidas = config_compras(datas['jan_ano_atual'], datas['dez_ano_atual'], casa)
    df_valoracao_estoque = config_valoracao_estoque_ou_producao('estoque', datas['jan_ano_atual'], datas['dez_ano_atual'], casa)
    df_transf_e_gastos, saida_alimentos, saida_bebidas, entrada_alimentos, entrada_bebidas, consumo_interno, quebras_e_perdas = config_transferencias_gastos(datas['jan_ano_atual'], datas['dez_ano_atual'], casa)
    df_valoracao_producao = config_valoracao_estoque_ou_producao('producao', datas['jan_ano_atual'], datas['dez_ano_atual'], casa)
    
    # Cálculo CMV para meses anteriores
    df_calculo_cmv = merge_e_calculo_para_cmv(
        df_faturamento_zig, 
        df_compras, 
        df_valoracao_estoque, 
        df_transf_e_gastos, 
        df_valoracao_producao, 
        df_faturamento_eventos
    )
    
    df_cmv_meses_anteriores_seguintes = calcula_cmv_proximos_meses(df_faturamento_meses_futuros, df_calculo_cmv, datas['ano_atual'], datas['mes_atual'])
    
    # Prepara para exibir CMV prox meses
    with st.container(border=True):
        st.markdown(f'''
            <h3>CMV</h3>
            <p><strong>Premissa:</strong> Média do % da despesa em relação ao Faturamento Real (A&B) dos últimos 2 meses x o valor estimado de Faturamento para o mês.</p>
        ''', unsafe_allow_html=True)
        
        # st.latex(r'''
        #     \\[0.5cm]
        #     \text{CMV Percentual Projetado} = \frac{CMV_1 + CMV_2}{Faturamento\ A\&B_1 + Faturamento\ A\&B_2}
        #     \\[0.5cm]
        #     \text{CMV Projetado} = \text{Faturamento Projetado} \times \text{CMV Percentual Projetado}
        #     \\[0.5cm]
        # ''')

        exibe_cmv_meses_anteriores_e_seguintes(df_cmv_meses_anteriores_seguintes, 'meses seguintes', datas['mes_atual'])

    st.divider()
   
    # Container que exibe faturamento e CMV real e projetado dos meses anteriores 
    with st.container(border=True):
        exibe_faturamento_meses_anteriores(df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])

        # Prepara para exibir CMV dos meses anteriores para comparação
        st.markdown(f'''
                <h5>Comparação CMV: CMV Projetado e CMV Real</h5>
            ''', unsafe_allow_html=True)
        
        exibe_cmv_meses_anteriores_e_seguintes(df_cmv_meses_anteriores_seguintes, 'meses anteriores', datas['mes_atual'])


###################### CUSTOS ARTÍSTICO GERAL - PRÓXIMOS MESES ###################### 
with tab3:
    df_custos_gerais = GET_CUSTOS_CLASS_CONT_GERAL()
    
    df_custos_faturamentos_mensais_passados = prepara_dados_custos_mensais(df_custos_gerais, df_faturamento_meses_futuros, casa)
    
    df_projecao_custos_meses_anteriores_seguintes = projecao_custos_proximos_meses(df_custos_faturamentos_mensais_passados, datas['ano_atual'], datas['mes_atual'])
    # st.write(df_projecao_custos_meses_anteriores_seguintes)

    st.markdown(f'''
        <h3>Projeções - {casa} - Próximos meses</h3>
        <h4>Custos Artístico Geral</h4>
        ''', unsafe_allow_html=True)
    st.divider()

    # Prepara para exibir projeção de custos dos prox meses
    exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_meses_anteriores_seguintes, 'meses seguintes', datas['ano_atual'], datas['mes_atual'])
    
    st.divider()
    
    st.markdown(f'''
            <h4>Meses anteriores</h4>
            <h5>Comparação: Custos Projetados e Custos Reais</h5>
        ''', unsafe_allow_html=True)
    
    # Prepara para exibir a projeção de custos dos meses anteriores - comparação
    exibe_custos_meses_anteriores_e_seguintes(df_projecao_custos_meses_anteriores_seguintes, 'meses anteriores', datas['ano_atual'], datas['mes_atual'])

