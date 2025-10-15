import streamlit as st
import pandas as pd
import datetime
import calendar
import locale
from datetime import timedelta
from utils.functions.forecast import *
from utils.functions.general_functions import config_sidebar
from utils.functions.general_functions_conciliacao import *
from utils.constants.general_constants import casas_validas
from utils.queries_conciliacao import GET_CASAS
from utils.queries_forecast import *

locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')

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

st.title(":material/event_upcoming: Forecast")
st.divider()


# Recuperando dados
df_casas = GET_CASAS()
(df_faturamento_agregado, 
 df_faturamento_eventos, 
 df_parc_receitas_extr, 
 df_parc_receit_extr_dia) = GET_TODOS_FATURAMENTOS(casas_validas)
df_orcamentos = GET_ORCAMENTOS()


# Filtrando Data
today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
amanha = today + timedelta(days=1)

mes_atual = today.month # numero
nome_mes_atual = datetime.datetime.now().strftime('%B').capitalize() # nome em português

ano_atual = today.year
ano_passado = today.year - 1

jan_ano_atual = datetime.datetime(today.year, 1, 1)
ultimo_dia_mes_atual = calendar.monthrange(today.year, today.month)[1] # numero
inicio_do_mes_atual = datetime.datetime(today.year, today.month, 1)
fim_do_mes_atual = datetime.datetime(today.year, today.month, ultimo_dia_mes_atual)

if mes_atual == 1:
    mes_anterior = 12
    ano_anterior = ano_atual - 1

else:
    mes_anterior = mes_atual - 1
    ano_anterior = ano_atual

inicio_do_mes_anterior = datetime.datetime(ano_anterior, mes_anterior, 1)

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


tab1, tab2 = st.tabs(['Mês corrente', 'Próximos meses'])

# Projeção de Faturamento - Mês corrente
with tab1:
    st.markdown(f'''
        <h4>Projeção de Faturamento - {casa} - {amanha.strftime('%d/%m/%Y')} a {fim_do_mes_atual.strftime('%d/%m/%Y')}</h4>
        <p>Por dia da semana, é calculada a média de faturamento baseada nas das duas últimas semanas.</p>
        ''', unsafe_allow_html=True)
    st.divider()

    # Prepara df de faturamento agregado
    df_faturamento_agregado_casa = df_faturamento_agregado[df_faturamento_agregado['ID_Casa'] == id_casa]
    df_faturamento_agregado_casa['Data_Evento'] = pd.to_datetime(df_faturamento_agregado_casa['Data_Evento'], errors='coerce')
    df_faturamento_agregado_casa['Dia_Semana'] = pd.to_datetime(df_faturamento_agregado_casa['Data_Evento'], errors='coerce').dt.strftime('%A')
    df_faturamento_agregado_casa['Dia_Mes'] = pd.to_datetime(df_faturamento_agregado_casa['Data_Evento'], errors='coerce').dt.day
    # st.write(df_faturamento_agregado_casa)

    # Filtra por casa e mês (apenas corrente) - para exibir
    df_faturamento_agregado_mes_corrente = df_faturamento_agregado_casa[
        (df_faturamento_agregado_casa['Data_Evento'] >= inicio_do_mes_atual) &
        (df_faturamento_agregado_casa['Data_Evento'] <= today)]
    
    st.markdown(f'''
        <h4>Dias anteriores - {inicio_do_mes_atual.strftime('%d/%m/%y')} a {today.strftime('%d/%m/%y')}</h4>
    ''', unsafe_allow_html=True)

    df_faturamento_dias_anteriores = df_faturamento_agregado_mes_corrente[['Categoria', 'Data_Evento', 'Dia_Semana', 'Valor_Bruto', 'Desconto', 'Valor_Liquido']]
    df_faturamento_dias_anteriores = df_faturamento_dias_anteriores.sort_values(by=['Categoria', 'Data_Evento'])
    dataframe_aggrid(
        df=df_faturamento_dias_anteriores,
        name=f"Projeção - Faturamento Dias Anteriores",
        num_columns=['Valor_Bruto', 'Desconto', 'Valor_Liquido'],     
        date_columns=['Data_Evento'],
        fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        fit_columns_on_grid_load=True   
    )
    st.divider()

    # Filtra por casa e mês (anterior e corrente) - para utilizar no cálculo de projeção
    df_faturamento_agregado_mes_corrente = df_faturamento_agregado_casa[
        (df_faturamento_agregado_casa['Data_Evento'] >= inicio_do_mes_anterior) &
        (df_faturamento_agregado_casa['Data_Evento'] <= fim_do_mes_atual)]
    

    # --- CRIA COMBINAÇÃO DE TODAS AS CATEGORIAS x DIAS (mês anterior e corrente) ---
    df_dias_futuros_com_categorias = lista_dias_mes_anterior_atual(ano_atual, mes_atual, ultimo_dia_mes_atual, 
    ano_anterior, mes_anterior,
    df_faturamento_agregado_mes_corrente)


    # Gera projeção para prox dias do mês corrente por dia da semana
    df_dias_futuros_mes = cria_projecao_mes_corrente(df_faturamento_agregado_mes_corrente, df_dias_futuros_com_categorias, today)


    ## A&B
    exibe_categoria_faturamento('A&B', df_dias_futuros_mes, today)

    ## Gifts
    exibe_categoria_faturamento('Gifts', df_dias_futuros_mes, today)

    ## Delivery
    exibe_categoria_faturamento('Delivery', df_dias_futuros_mes, today)

    ## Artístico - Couvert
    exibe_categoria_faturamento('Couvert', df_dias_futuros_mes, today)

    ## Eventos
    st.markdown(f'''
        <h4 style="color: #1f77b4;">Faturamento Eventos</h4>
    ''', unsafe_allow_html=True)

    # exibe_categoria_faturamento('Eventos', df_dias_futuros_mes, today)
    df_faturamento_eventos_futuros = df_faturamento_eventos[
        (df_faturamento_eventos['ID_Casa'] == id_casa) &
        (df_faturamento_eventos['Data_Evento'] >= amanha) &
        (df_faturamento_eventos['Data_Evento'] <= fim_do_mes_atual) 
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
        st.info(f'Não há informações de eventos para os próximos dias de {nome_mes_atual}.')
    st.divider()

    ## Outras Receitas
    st.markdown(f'''
        <h4 style="color: #1f77b4;">Outras Receitas</h4>
    ''', unsafe_allow_html=True)

    # Filtra por casa e dias futuros
    df_parc_receitas_extr_futuras = df_parc_receit_extr_dia[
        (df_parc_receit_extr_dia['ID_Casa'] == id_casa) &
        (df_parc_receit_extr_dia['Data_Evento'] >= amanha) &
        (df_parc_receit_extr_dia['Data_Evento'] <= fim_do_mes_atual) 
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
        st.info(f'Não há informações de receitas extraordinárias para os próximos dias de {nome_mes_atual}.')


    # Orçamentos
    # df_orcamentos_filtrado = df_orcamentos[
    #     (df_orcamentos['ID_Casa'] == id_casa) &
    #     (df_orcamentos['Ano'] == ano_atual) & 
    #     (df_orcamentos['Mes'] == mes_atual)]
    # st.write(df_orcamentos_filtrado)


# Projeção de Faturamento - Próximos meses
with tab2:
    st.markdown(f'''
        <h4>Projeção de Faturamento - {casa} - Próximos meses</h4>
        <p>Média do % de atingimento do Faturamento Real dos últimos dois meses x Orçamento.</p>
        ''', unsafe_allow_html=True)
    st.divider()