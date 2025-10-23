import streamlit as st
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


tab1, tab2, tab3 = st.tabs(['Faturamento - Mês corrente', 'Faturamento - Próximos meses', 'CMV - Próximos meses'])

# Projeção de Faturamento - Mês corrente
with tab1:
    st.markdown(f'''
        <h4>Projeção de Faturamento - {casa} - {datas['amanha'].strftime('%d/%m/%Y')} a {datas['fim_mes_atual'].strftime('%d/%m/%Y')}</h4>
        <p><strong>Premissa</strong> (para todas as categorias de faturamento, exceto 'Eventos' e 'Outras Receitas'): por dia da semana, é calculada a média de faturamento baseada nas das duas últimas semanas.</p>
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

    ## A&B
    exibe_categoria_faturamento('A&B', df_dias_futuros_mes, datas['today'])

    ## Gifts
    exibe_categoria_faturamento('Gifts', df_dias_futuros_mes, datas['today'])

    ## Delivery
    exibe_categoria_faturamento('Delivery', df_dias_futuros_mes, datas['today'])

    ## Artístico - Couvert
    exibe_categoria_faturamento('Couvert', df_dias_futuros_mes, datas['today'])

    ## Eventos
    st.markdown(f'''
        <h4 style="color: #1f77b4;">Faturamento Eventos</h4>
        <p><strong>Premissa:</strong> considerar o que está lançado para a competência nesse mês</p>        
    ''', unsafe_allow_html=True)

    df_faturamento_eventos_futuros = df_faturamento_eventos[
        (df_faturamento_eventos['ID_Casa'] == id_casa) &
        (df_faturamento_eventos['Data_Evento'] >= datas['amanha']) &
        (df_faturamento_eventos['Data_Evento'] <= datas['fim_mes_atual']) 
    ]

    df_faturamento_eventos_futuros = df_faturamento_eventos_futuros[['Categoria', 'Data_Evento', 'Valor_Bruto', 'Desconto', 'Valor_Liquido']]
    if not df_faturamento_eventos_futuros.empty:
        dataframe_aggrid(
            df=df_faturamento_eventos_futuros,
            name=f"Projeção - Faturamento Eventos",
            num_columns=['Valor_Bruto', 'Desconto', 'Valor_Liquido'],     
            date_columns=['Data_Evento'],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True   
        )
    else:
        st.info(f"Não há informações de eventos para os próximos dias de {datas['nome_mes_atual_pt']}.")
    st.divider()

    ## Outras Receitas
    st.markdown(f'''
        <h4 style="color: #1f77b4;">Outras Receitas</h4>
        <p><strong>Premissa:</strong> considerar o que está lançado para a competência nesse mês</p>
    ''', unsafe_allow_html=True)

    # Filtra por casa e dias futuros
    df_parc_receitas_extr_futuras = df_parc_receit_extr_dia[
        (df_parc_receit_extr_dia['ID_Casa'] == id_casa) &
        (df_parc_receit_extr_dia['Data_Evento'] >= datas['amanha']) &
        (df_parc_receit_extr_dia['Data_Evento'] <= datas['fim_mes_atual']) 
    ]

    if not df_parc_receitas_extr_futuras.empty:
        # Merge para exibir categorias específicas no expander
        df_detalha_outras_receitas = df_parc_receitas_extr_futuras.merge(
            df_parc_receitas_extr,
            how='left',
            left_on=['Casa', 'Data_Evento'],
            right_on=['Casa', 'Data_Ocorrencia']
        )
        df_detalha_outras_receitas = df_detalha_outras_receitas[['Categoria_x', 'Data_Ocorrencia', 'Categoria_y', 'Valor_Parcela']]
        df_detalha_outras_receitas = df_detalha_outras_receitas.rename(columns={'Categoria_y':'Classificacao_Receita', 'Categoria_x':'Categoria'})

        # Exibe df de 'Outras Receitas'
        df_parc_receitas_extr_futuras = df_parc_receitas_extr_futuras[['Categoria', 'Data_Evento', 'Valor_Bruto', 'Desconto', 'Valor_Liquido']]
        dataframe_aggrid(
                df=df_parc_receitas_extr_futuras,
                name=f"Projeção - Faturamento Outras Receitas",
                num_columns=['Valor_Bruto', 'Desconto', 'Valor_Liquido'],     
                date_columns=['Data_Evento'],
                fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
                fit_columns_on_grid_load=True   
            )

        with st.expander('Detalhamento', icon=":material/chevron_right:"):
            df_detalha_outras_receitas_fmt = formata_df(df_detalha_outras_receitas)
            st.dataframe(df_detalha_outras_receitas_fmt, hide_index=True)
        
    else:
        st.info(f"Não há informações de receitas extraordinárias para os próximos dias de {datas['nome_mes_atual_pt']}.")
    st.divider()


    # Filtra para exibir dias anteriores do mês corrente - para comparação projeção/real
    df_faturamento_dias_anteriores = df_dias_futuros_mes[
        (df_dias_futuros_mes['Data_Evento'] >= datas['inicio_mes_atual']) &
        (df_dias_futuros_mes['Data_Evento'] <= datas['today'])]
    
    # Organiza colunas
    df_faturamento_dias_anteriores = df_faturamento_dias_anteriores[['Categoria', 'Data_Evento', 'Dia Semana', 'Projecao', 'Valor_Bruto', 'Desconto', 'Valor_Liquido']]
    df_faturamento_dias_anteriores = df_faturamento_dias_anteriores.sort_values(by=['Categoria', 'Data_Evento'])
    df_faturamento_dias_anteriores = df_faturamento_dias_anteriores.rename(
        columns={'Projecao':'Faturamento Projetado', 
                 'Valor_Bruto':'Faturamento Real',
                 'Valor_Liquido':'Faturamento Liquido'})

    st.markdown(f'''
        <h4>Dias anteriores - {datas['inicio_mes_atual'].strftime('%d/%m/%y')} a {datas['today'].strftime('%d/%m/%y')}</h4>
        <h5>Comparação: Faturamento Projetado e Faturamento Real</h5>
    ''', unsafe_allow_html=True)

    dataframe_aggrid(
        df=df_faturamento_dias_anteriores,
        name=f"Projeção - Faturamento Dias Anteriores",
        num_columns=['Faturamento Projetado', 'Faturamento Real', 'Desconto', 'Faturamento Liquido'],     
        date_columns=['Data_Evento'],
        fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        fit_columns_on_grid_load=True   
    )


# Projeção de Faturamento - Próximos meses
with tab2:
    # Dados - Faturamento e Orçamento Mensal
    df_orcamentos = GET_ORCAMENTOS()
    df_faturamento_agregado_mes = GET_TODOS_FATURAMENTOS_MENSAL(df_faturamento_eventos, df_parc_receit_extr_dia)

    st.markdown(f'''
        <h4>Projeção de Faturamento - {casa} - Próximos meses</h4>
        <p><strong>Premissa</strong> (para todas as categorias de faturamento): média do percentual (%) de atingimento do Faturamento Real dos últimos dois meses x Orçamento.</p>
        ''', unsafe_allow_html=True)
    st.divider()

    # Prepara df de faturamento agregado mensal para a casa selecionada
    df_faturamento_mes_casa, df_faturamento_orcamento = prepara_dados_faturamento_orcamentos_mensais(id_casa, df_orcamentos, df_faturamento_agregado_mes, datas['ano_passado'], datas['ano_atual'])


    # --- CRIA COMBINAÇÃO DE TODAS AS CATEGORIAS x MESES (ano corrente) ---
    df_meses_futuros_com_categorias = lista_meses_ano(df_faturamento_mes_casa, datas['ano_atual'], datas['ano_passado'])


    # Gera projeção para prox meses do ano
    df_faturamento_meses_futuros = cria_projecao_meses_seguintes(df_faturamento_orcamento, df_meses_futuros_com_categorias, datas['ano_atual'])

    ## A&B
    exibe_categoria_faturamento_prox_meses('A&B', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])

    ## Gifts
    exibe_categoria_faturamento_prox_meses('Gifts', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])

    ## Delivery
    exibe_categoria_faturamento_prox_meses('Delivery', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])

    ## Artístico - Couvert
    exibe_categoria_faturamento_prox_meses('Couvert', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])

    ## Eventos
    exibe_categoria_faturamento_prox_meses('Eventos', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])

    ## Outras Receitas
    exibe_categoria_faturamento_prox_meses('Outras Receitas', df_faturamento_meses_futuros, datas['ano_atual'], datas['mes_atual'])
   

    # Exibie meses anteriores do ano - para comparação projeção/real
    st.markdown(f'''
            <h4>Meses anteriores</h4>
            <h5>Comparação: Atingimento Projetado e Atingimento Real</h5>
        ''', unsafe_allow_html=True)
    
    df_faturamento_meses_anteriores = df_faturamento_meses_futuros.copy()
    df_faturamento_meses_anteriores = df_faturamento_meses_anteriores[
        (df_faturamento_meses_anteriores['Ano'] == datas['ano_atual']) &
        (df_faturamento_meses_anteriores['Mes'] <= datas['mes_atual'])
    ]

    df_faturamento_meses_anteriores = df_faturamento_meses_anteriores[['Categoria', 'Mes', 'Orcamento_Faturamento', 'Valor_Bruto', 'Atingimento Real (%)', 'Projecao_Atingimento (%)', 'Valor Projetado']]
    df_faturamento_meses_anteriores = df_faturamento_meses_anteriores.rename(columns={
        'Mes':'Mês',
        'Orcamento_Faturamento':'Orçamento',
        'Valor_Bruto':'Faturamento Real',
        'Projecao_Atingimento (%)':'Atingimento Projetado (%)',
        'Valor Projetado':'Faturamento Projetado'
    })
    df_faturamento_meses_anteriores = df_faturamento_meses_anteriores.sort_values(by=['Categoria', 'Mês'])

    dataframe_aggrid(
        df=df_faturamento_meses_anteriores,
        name=f"Projeção - Faturamento Meses Anteriores",
        num_columns=['Orçamento', 'Faturamento Real', 'Faturamento Projetado'],     
        percent_columns=['Atingimento Real (%)', 'Atingimento Projetado (%)'],
        fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        fit_columns_on_grid_load=True   
    )


# Projeção de CMV - Próximos meses
with tab3:
    # st.markdown(f'''
    #     <h4>Projeção de CMV - {casa} - {datas['amanha'].strftime('%d/%m/%Y')} a {datas['fim_mes_atual'].strftime('%d/%m/%Y')}</h4>
    #     <p><strong>Premissa</strong></p>
    #     ''', unsafe_allow_html=True)
    st.divider()

    df_faturamento_zig, faturamento_bruto_alimentos, faturamento_bruto_bebidas, faturamento_delivery = config_faturamento_bruto_zig(df_faturamento_agregado_dia, datas['jan_ano_atual'], datas['dez_ano_atual'], casa)
    # NAO OK df_faturamento_eventos, faturamento_alimentos_eventos, faturamento_bebidas_eventos = config_faturamento_eventos(datas['jan_ano_atual'], datas['dez_ano_atual'], casa, faturamento_bruto_alimentos, faturamento_bruto_bebidas)
    
    df_compras, compras_alimentos, compras_bebidas = config_compras(datas['jan_ano_atual'], datas['dez_ano_atual'], casa)
    
    df_valoracao_estoque = config_valoracao_estoque_ou_producao('estoque', datas['jan_ano_atual'], datas['dez_ano_atual'], casa)
    # OK df_valoracao_estoque_mes_anterior = config_valoracao_estoque(datas['inicio_mes_anterior'], datas['ultimo_dia_mes_anterior'], casa)
    # OK df_variacao_estoque, variacao_estoque_alimentos, variacao_estoque_bebidas = config_variacao_estoque(df_valoracao_estoque_atual, df_valoracao_estoque_mes_anterior)
    
    df_transf_e_gastos, saida_alimentos, saida_bebidas, entrada_alimentos, entrada_bebidas, consumo_interno, quebras_e_perdas = config_transferencias_gastos(datas['jan_ano_atual'], datas['dez_ano_atual'], casa)
    
    df_valoracao_producao = config_valoracao_estoque_ou_producao('producao', datas['jan_ano_atual'], datas['dez_ano_atual'], casa)
    # OK df_producao_alimentos_mes_anterior, df_producao_bebidas_mes_anterior, valor_producao_alimentos_mes_anterior, valor_producao_bebidas_mes_anterior = config_valoracao_producao(datas['inicio_mes_anterior'], casa)
    # OK df_diferenca_producao_alimentos = config_diferenca_producao(df_producao_alimentos, df_producao_alimentos_mes_anterior)
    # OK df_diferenca_producao_bebidas = config_diferenca_producao(df_producao_bebidas, df_producao_bebidas_mes_anterior)

    # # Cálculos
    # diferenca_producao_alimentos = valor_producao_alimentos - valor_producao_alimentos_mes_anterior
    # diferenca_producao_bebidas = valor_producao_bebidas - valor_producao_bebidas_mes_anterior

    # cmv_alimentos = compras_alimentos - variacao_estoque_alimentos - saida_alimentos + entrada_alimentos - consumo_interno - diferenca_producao_alimentos
    # cmv_bebidas = compras_bebidas - variacao_estoque_bebidas - saida_bebidas + entrada_bebidas - diferenca_producao_bebidas
    # cmv_alimentos_e_bebidas = cmv_alimentos + cmv_bebidas
    
    # faturamento_total_alimentos = faturamento_bruto_alimentos + faturamento_alimentos_delivery + faturamento_alimentos_eventos
    # faturamento_total_bebidas = faturamento_bruto_bebidas + faturamento_bebidas_delivery + faturamento_bebidas_eventos

    # st.write(df_valoracao_estoque)
